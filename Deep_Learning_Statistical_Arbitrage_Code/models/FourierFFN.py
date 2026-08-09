import torch
import torch.nn as nn


class FourierFFN(nn.Module):
    """A Feed Forward Neural Network designed to process Fourier features.
    
    This model consists of multiple fully connected layers with ReLU activation
    and dropout, followed by a final linear layer that outputs a single value.
    
    Args:
        logdir (str): Directory path for saving logs and model checkpoints
        lookback (int, optional): Number of historical time steps to consider. Defaults to 30.
        random_seed (int, optional): Seed for reproducibility. Defaults to 0.
        device (str, optional): Device to run the model on ('cpu' or 'cuda'). Defaults to "cpu".
        hidden_units (list[int], optional): List specifying the size of each hidden layer.
            Defaults to [30, 16, 8, 4]. Each number represents the number of neurons in that layer.
        dropout (float, optional): Dropout probability for regularization. Defaults to 0.25.
            Must be between 0 and 1.
    
    Attributes:
        is_trainable (bool): Indicates if the model can be trained
        is_frictions_model (bool): Indicates if the model accounts for trading frictions
        hidden_layers (nn.ModuleList): List of hidden layer blocks, each containing:
            - Linear layer
            - ReLU activation
            - Dropout
        final_layer (nn.Linear): Final linear layer producing the output prediction
    """

    def __init__(
        self,
        lookback: int = 30,
        random_seed: int = 0,
        device: str = "cpu",
        hidden_units: list[int] = [30, 16, 8, 4],
        dropout: float = 0.25,
    ):
        super(FourierFFN, self).__init__()
        self.is_trainable = True
        self.is_frictions_model = False

        self.random_seed = random_seed
        torch.manual_seed(self.random_seed)
        self.device = torch.device(device)
        self.hidden_units = hidden_units

        self.hidden_layers = nn.ModuleList()
        for i in range(len(hidden_units) - 1):
            self.hidden_layers.append(
                nn.Sequential(
                    nn.Linear(hidden_units[i], hidden_units[i + 1]),
                    nn.ReLU(True),
                    nn.Dropout(dropout),
                )
            )
        self.final_layer = nn.Linear(hidden_units[-1], 1)

        self.is_trainable = True
        self.is_frictions_model = False
                
    def forward(self,x):
        """Forward pass of the network.
        
        Args:
            x (torch.Tensor): Input tensor of shape (batch_size, hidden_units[0])
                where hidden_units[0] is the size of the first layer (default: 30)
        
        Returns:
            torch.Tensor: Output predictions of shape (batch_size,)
                A single value per input sample representing the predicted value
                
        Note:
            The input tensor x should match the size of the first hidden layer.
            The model processes through each hidden layer sequentially, applying:
            1. Linear transformation
            2. ReLU activation
            3. Dropout
            Finally, it passes through the final layer to produce a single output value.
        """
        for i in range(len(self.hidden_units)-1):
            x = self.hidden_layers[i](x)
        return self.final_layer(x).squeeze()
