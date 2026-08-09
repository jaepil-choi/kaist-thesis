import torch
import torch.nn as nn


class CNN_Block(nn.Module):
    def __init__(self, in_filters=1, out_filters=8, normalization=True, filter_size=2):
        super(CNN_Block, self).__init__() 
        self.is_trainable = True
        self.is_frictions_model = True
         
        self.in_filters = in_filters
        self.out_filters = out_filters
        
        self.conv1 = nn.Conv1d(in_channels=in_filters, out_channels=out_filters, kernel_size=filter_size,
                                    stride=1, padding=0, dilation=1, groups=1, bias=True, padding_mode='zeros')
        self.conv2 = nn.Conv1d(in_channels=out_filters, out_channels=out_filters, kernel_size=filter_size,
                                    stride=1, padding=0, dilation=1, groups=1, bias=True, padding_mode='zeros')
        self.relu = nn.ReLU(inplace=True)
        self.left_zero_padding = nn.ConstantPad1d((filter_size-1,0),0)
        
        self.normalization1 = nn.InstanceNorm1d(in_filters)
        self.normalization2 = nn.InstanceNorm1d(out_filters)
        self.normalization = normalization
       
    def forward(self, x):  # x and out have dims (N,C,T) where C is the number of channels/filters
        if self.normalization:
            x = self.normalization1(x)
        out = self.left_zero_padding(x)
        out = self.conv1(out)
        out = self.relu(out)
        if self.normalization: 
            out = self.normalization2(out)
        out = self.left_zero_padding(out)
        out = self.conv2(out)
        out = self.relu(out)
        out = out + x.repeat(1,int(self.out_filters/self.in_filters),1)   
        return out 

class WeightsTransformer(nn.Module):
    def __init__(self,
                 d_model=8, 
                 nhead=4, 
                 dim_feedforward=2*8,
                 dropout=0.25):
        super(WeightsTransformer, self).__init__()
        self.is_trainable = True
        self.is_frictions_model = True

        self.self_attn = nn.MultiheadAttention(d_model, nhead)
        self.linear1 = nn.Linear(d_model+1, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model+1)

        self.norm1 = nn.LayerNorm(d_model+1)
        self.norm2 = nn.LayerNorm(d_model+1)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.activation = nn.ReLU(inplace=True)
        
    def forward(self, src, old_weights):
        src2 = self.self_attn(src, src, src)[0][-1]  # (L, N, E) where L lookback, N is the batch size, E is the embedding dimension.
        N,E = src2.shape
        src = src[-1] + self.dropout1(src2)
        old_weights = old_weights.reshape((N,1))
        src = torch.cat((src,old_weights),1)  # (N,E+1)
        src = self.norm1(src)
        src2 = self.linear2(self.dropout(self.activation(self.linear1(src))))
        src = src + self.dropout2(src2)
        src = self.norm2(src)
        return src


class CNNTransformerFrictions(nn.Module):
    def __init__(
        self,
        random_seed=0,
        lookback=30,
        device="cpu",  # other options for device are e.g. "cuda:0"
        normalization_conv=True,
        filter_numbers=[1, 8],
        attention_heads=4,
        use_convolution=True,
        hidden_units=2 * 8,
        hidden_units_factor=2,
        dropout=0.25,
        filter_size=2,
        use_transformer=True,
    ):
        
        super(CNNTransformerFrictions, self).__init__()
        self.is_trainable = True
        self.is_frictions_model = True

        if hidden_units and hidden_units_factor and hidden_units != hidden_units_factor * filter_numbers[-1]:
            raise Exception("`hidden_units` conflicts with `hidden_units_factor`; provide one or the other, but not both.")
        if hidden_units_factor:
            hidden_units = hidden_units_factor * filter_numbers[-1]
        self.random_seed = random_seed 
        torch.manual_seed(self.random_seed)
        self.device = torch.device(device)
        self.filter_numbers = filter_numbers
        self.use_transformer = use_transformer
        self.use_convolution = use_convolution and len(filter_numbers) > 0
        
        self.convBlocks = nn.ModuleList()
        for i in range(len(filter_numbers)-1):
            self.convBlocks.append(
                CNN_Block(filter_numbers[i], filter_numbers[i+1], normalization=normalization_conv, filter_size=filter_size)
            )
        self.encoder = WeightsTransformer(d_model=filter_numbers[-1], nhead=attention_heads, dim_feedforward=hidden_units, dropout=dropout)
        self.linear = nn.Linear(filter_numbers[-1]+1,1)
                 
    def forward(self, x, old_weights):  # x has dimension (N,T), oldWeights has dimension N
        N,T = x.shape
        x = x.reshape((N,1,T))  # (N,1,T)
        if self.use_convolution:
            for i in range(len(self.filter_numbers)-1):
                x = self.convBlocks[i](x)  # (N,C,T), C is the number of channels/features
        x = x.permute(2,0,1)
        if self.use_transformer:
            x = self.encoder(x, old_weights)  # the input of the transformer is (T,N,C)
        return self.linear(x).squeeze()