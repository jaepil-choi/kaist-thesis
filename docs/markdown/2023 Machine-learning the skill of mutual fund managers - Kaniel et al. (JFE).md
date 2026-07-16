# Machine-Learning the Skill of Mutual Fund Managers

Journal of Financial Economics 150 (2023) 94–138

Contents lists available at ScienceDirect

Journal  of  Financial  Economics

journal homepage: www.elsevier.com/locate/jfec

Machine-learning  the  skill  of  mutual  fund  managers

✩

Ron Kaniel a , b , c , Zihan Lin d , Markus Pelger e , Stijn Van Nieuwerburgh f , ∗
a
Simon School of Business, Rochester University, 300 Wilson Blvd, Rochester, NY 14620 USA
b
Fanhai International School of Finance, Fudan, Shanghai 20 0 0 01, China
c
Arison School of Business, Reichman University, Herzliya 4610101, Israel
d
Institute for Computational and Mathematical Engineering, Stanford University, 475 Via Ortega, Stanford, CA 94305, USA
e
Department of Management Science and Engineering, Stanford University, 475 Via Ortega, Stanford, CA 94305, USA
f
Columbia Business School, 665 West 130 Street, New York, NY 10027l, USA

a r t i c l e

i n f o

## Abstract

We show, using machine learning, that fund characteristics can consistently differentiate
high from low-performing mutual funds, before and after fees. The outperformance per-
sists for more than three years. Fund momentum and fund ﬂow are the most important
predictors of future risk-adjusted fund performance, while characteristics of the stocks that
funds hold are not predictive. Returns of predictive long-short portfolios are higher follow-
ing a period of high sentiment. Our estimation with neural networks enables us to uncover
novel and substantial interaction effects between sentiment and both fund ﬂow and fund
momentum.

© 2023 Elsevier B.V. All rights reserved.

Article history:
Received 10 April 2023
Revised 27 July 2023
Accepted 31 July 2023
Available online 11 August 2023

JEL classiﬁcation:
G11
G12
G17
G23
C45

Keywords:
Mutual fund performance
Fund ﬂow
Momentum
Machine learning
Sentiment
Big data
Neural networks

## 1. Introduction

The asset management industry is enormous and grow-
ing  rapidly.  U.S.  mutual  funds  had  $24  trillion  in  assets

✩

Nikolai Roussanov was the editor for this article. The authors would
like to thank Will Cong, Kay Giesecke, Stefano Giglio, Markus Ibert (dis-
cussant), Allan Timmermann (discussant), Alberto Rossi (discussant), and
seminar and conference participants at Imperial College London, Oxford,
Stanford, the Annual Society for Financial Econometrics Conference, the
BI-SHoF Conference,  the  Conference  on  Emerging  Technologies  in  Ac-
counting and Financial Economies, and the NBER Summer Institute in Big
Data for helpful comments.
∗ Corresponding author.

E-mail addresses: ron.kaniel@simon.rochester.edu (R. Kaniel), zihanl@
stanford.edu (Z. Lin), mpelger@stanford.edu (M. Pelger), svnieuwe@gsb.
columbia.edu (S. Van Nieuwerburgh) .

https://doi.org/10.1016/j.jﬁneco.2023.07.004
0304-405X/© 2023 Elsevier B.V. All rights reserved.

under  management  at  the  end  of  2020,  more  than  half
of  which  were  in  equity  mutual  funds.  Over  100  mil-
lion Americans rely on such funds to save for retirement
and  meet  other  ﬁnancial  objectives.  Many  of  these  mu-
tual funds actively trade stocks in an effort to out-perform
their benchmarks and create value for their investors. The
literature has found mixed results in terms of the invest-
ment performance of actively-traded equity mutual funds.
We revisit the evidence using modern techniques, and ask
which–if  any–characteristics  of  mutual  funds  and  of  the
stocks they hold can help separate the corn from the chaff.
We uncover new evidence of economically substantial and
long-lasting abnormal return predictability. Fund ﬂows and
fund return momentum are the main two characteristics
that can meaningfully and robustly help distinguish funds

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

that  outperform  from  those  that  under-perform,  particu-
larly in times of high investor sentiment.

We  study  the  universe  of  actively-traded  U.S.  equity
mutual funds between 1980 and 2019 and the stocks that
they  hold.  The  object  we  predict  is  the  abnormal  fund
return,  deﬁned  as  the  locally-estimated  four-factor  alpha
of  the  mutual  fund.  The  predictors  are  a  long  list  of  46
stock  characteristics  weighted  by  the  funds’  holdings  of
each stock and 13 fund and fund-family characteristics. We
also include a variable that summarizes the overall state
of the market, either proxied by investor sentiment or by
a comprehensive measure of macro-economic activity. Our
main method is a feedforward neural network, which can
reliably estimate a complex functional relationship among
a  large  set  of  predictors.  It  is  trained  and  tuned  on  one
subset  of  the  data  and  evaluated  on  another  subset  of
the data. Hence, all of our predictions are out-of-sample.
Our method identiﬁes fund characteristic information, and
speciﬁcally fund ﬂow and fund momentum, as the key pre-
dictors  of  mutual  fund  out-performance.  Moreover,  there
is an important interaction effect between these two fund
characteristics and sentiment, which linear models fail to
pick up.

The model generates large differences in out-of-sample
performance. Buying the ten percent of mutual funds with
the best predicted performance each month, and using the
model  not  only  to  select  but  also  to  weight  the  funds
within the top decile, generates a cumulative abnormal re-
turn of 72%. Buying the ten percent of mutual funds with
the worst predicted performance each month produces a
cumulative  abnormal  return  of  −119%.  The  191%  differ-
ence in out-of-sample performance based on the model’s
predictions  is  economically  large  and  statistically  signiﬁ-
cant.  It  translates  into  a  monthly  out-performance  of  15
basis  points  for  the  10%  best  funds  and  25  basis  points
per  month  under-performance  for  the  10%  worst  funds.
Since the best and the worst funds have similar fees, the
same result holds for after-fee abnormal returns. The per-
formance improves further when we directly predict net-
of-fees performance.

The  performance  differential  is  nearly  identical  if  we
constrain the model by removing all stock characteristic in-
formation. In fact, we can also remove most fund and fund
family characteristics. The predictions of a model that are
only given data on fund ﬂow, fund momentum, and senti-
ment are nearly as good as those of the full model. They
deliver out-performance of 48 basis points per month for
the top relative to the bottom deciles of predicted perform-
ers. The Sharpe ratio on this strategy is 0.24 per month.

The predictability we uncover is surprisingly persistent.
Even though investments are made based on one-month
ahead prediction, the best decile of funds signiﬁcantly out-
performs  the  worst  decile  for  three  years.  Even  after  36
months, the monthly Sharpe ratio on the long-short port-
folio is still 0.20, compared to a 0.30 Sharpe ratio 3-months
ahead. This result is remarkable in light of the literatures
diﬃculty in ﬁnding evidence for persistence in abnormal
fund returns.

We  decompose  the  fund  abnormal  return  into  a
between-disclosure  component,  which  holds  ﬁxed  the
funds’  stock  holdings  at  their  previous  quarter-end  val-

ues,  and  a  within-disclosure  component,  which  accounts
for  mutual  fund  trades  during  the  quarter.  The  latter  is
the sum of the return gap and a risk exposure differen-
tial. 1 We ﬁnd that about half of the outperformance comes
from the model’s ability to predict between-disclosure ab-
normal returns and the other half from predicting within-
disclosure abnormal returns. Both fund ﬂow and fund mo-
mentum predict the return gap and the risk exposure dif-
ferential, while most stock characteristics that predict the
return gap do so by taking on more systematic risk result-
ing in little within-disclosure abnormal return. These re-
sults shed additional light on the sources and persistence
of out-performance.

The  salience  of  ﬂow  and  fund  return  momentum  as
the  key  predictors  suggests  that  some  investors  can  de-
tect  skill  and  (re)allocate  their  investment  towards  such
skilled  managers.  This  reallocation  of  investment  ﬂows
is  not  as  strong  as  the  frictionless  model  of  Berk  and
Green  (2004)  predicts.  Skill  leaves  a  trail  in  the  form  of
fund return momentum for investors to exploit in the next
period.  Put  differently,  the  ﬂows  are  gradual  and  small
enough  that  it  takes  several  periods  until  the  fund  runs
into zero marginal abnormal returns.

The  results  are  potentially  also  consistent  with  funds
and  fund  families  attracting  ﬂows  through  marketing
rather  than—or  in  addition  to—through  investment  skill
( Gallaher et al., 2009; Ibert et al., 2018; Roussanov et al.,
2021 ).  Marketing-induced  inﬂows  create  buying  pressure
for stocks that the fund typically invests in. In a world with
downward-sloping  demand  curves  ( Coval  and  Stafford,
2007;  Koijen  and  Yogo,  2019;  Gabaix  and  Koijen,  2021 ),
this raises prices and lifts fund returns. Through the ﬂow-
performance relationship, as well as through persistence in
marketing-driven ﬂows, the out-performance creates more
inﬂows in the next period. The demand pressure increases
prices further, generating momentum in fund returns. The
fact that ﬂows and fund momentum have a much stronger
association with fund performance in high-sentiment peri-
ods lends further credence to this marketing-driven chan-
nel.

Our paper makes several methodological contributions
adding  to  the  protocol  of  how  to  use  machine  learning
models  for  asset  pricing.  First,  we  contribute  to  relative
performance prediction. We show that abnormal returns,
obtained as local residuals to a factor model, are not only
an economically motivated, but also the statistically bet-
ter target for prediction. In contrast, the level of fund (and
stock) returns is extremely hard to predict. Abnormal re-
turns remove the level effect of market and other risk fac-
tors, which makes the prediction of abnormal returns a rel-
ative objective. The commonly-used machine learning pre-
diction of total returns can be dominated by the prediction
error in the common component in return levels, resulting
in suboptimal use of cross-sectional information relevant
to  relative  performance.  Indeed,  we  show  that  using  the
same ﬂexible methods for predicting abnormal returns in-

1

The return gap is the difference between the fund’s actual returns
over the period and the hypothetical returns generated by keeping the
fund’s portfolio holdings constant.

95

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

stead of total returns results in higher accuracy and better
portfolio performance.

Second, we quantify the economic beneﬁt of different
information  sets.  We  suggest  to  compare  the  prediction
and trading beneﬁts by varying the information set avail-
able to the same ﬂexible machine-learning algorithm. The
focus  is  the  comparison  of  information  sets  instead  of  a
horse race of model speciﬁcations.

Third, we show how to measure the dependencies on
macroeconomic  states.  Speciﬁcally,  we  propose  a  cross-
out-of-sample evaluation of conditional models using the
full time-series. Importantly, the data points for estimat-
ing  and  evaluating  the  model  have  to  be  sampled  such
that  all  relevant  economic  conditions  are  represented  in
all  subsamples,  which  can  be  achieved  by  random  sam-
pling  over  time.  This  is  particularly  important  for  mea-
suring the dependencies on macro-economic states which
are  only  available  in  a  subset  of  the  data  and  might  be
neglected in the estimation or evaluation with a conven-
tional chronological data split. Our evaluation approach al-
lows  us  to  take  advantage  of  all  sample  periods  for  the
out-of-sample analysis, diminishing the effect of particular
subperiods. That said, our main results are robust to using
a chronological cross-validation as well as an expanding-
window sampling approach.

Fourth, in order to better assess the investment bene-
ﬁts of prediction, we suggest prediction-weighted portfo-
lios. These portfolios result in the largest return spread as
they take advantage not only of the ranking but also of the
relative strength of the prediction signal. The prediction-
weighted  portfolios  dominate  the  widely-used  equally-
weighted portfolios based on prediction quantiles.

Last but not least, we propose a new measure for inter-
action effects in machine learning algorithms, which does
not  only  measure  a  local  slope,  but  a  more  informative
global slope. For this interpretable measure, we provide a
formal statistical signiﬁcance test based on functional cen-
tral limit theorems for neural networks.

Related  Literature .  An  enormous  literature  in  empir-
ical  asset  pricing  studies  whether  mutual  fund  man-
agers  outperform  their  benchmarks  through  stock  pick-
ing  and  market  timing.  The  seminal  paper  of  Berk  and
Green  (2004)  suggests  that  a  large  fraction  of  fund
managers  out-performs  before  fees  while  Fama  and
French  (2010)  ﬁnd  no  out-performance  before  fees.
Kacperczyk  et  al.  ( 2014;  2016 )  ﬁnd  that  a  modest  frac-
tion of managers displays enough skill to persistently out-
perform, through a strategy that switches between market
timing in recessions and stock picking in expansions. The
presence of uninformed mutual fund managers and retail
traders makes this possible as an equilibrium phenomenon
( Stambaugh, 2014 ).

While  investors  direct  ﬂows  to  funds  that  out-
perform,  at  least  as  measured  by  the  CAPM  alpha
( Berk  and  Van  Binsbergen,  2016;  Barber  et  al.,  2016 ),
there  is  mounting  evidence  that  other  factors  be-
sides  fees  and  before-fee  performance  determine  fund
ﬂows.  Gallaher  et  al.  (2009)  shows  advertising  im-
pacts  ﬂows  at  the  industry,  family  and  fund  level.
Roussanov  et  al.  (2021)  argues  that  marketing  is  an  im-
portant determinant of ﬂows, necessary to understand the

96

empirical joint distribution of fund size and performance.
Consistent  with  this,  Ibert  et  al.  (2018)  shows  that  fund
manager compensation is tied to the component of assets-
under-management that is orthogonal to current and past
fund performance.

The predictive role of ﬂows to fund performance was
ﬁrst uncovered by Gruber (1996) and Zheng (1999) , who
identiﬁed  a  positive,  but  fairly  short-lived  and  weak  re-
lationship.  The  “smart  money” relation  they  found  ex-
ists  for  small  but  not  for  large  funds.  Risk  adjustment
in  these  papers  did  not  include  momentum.  Sapp  and
Tiwari  (2004)  shows  the  smart  money  effect  disappears
once  a  stock  return  momentum  factor  is  considered
( Carhart, 1997 ). Prior work identiﬁed different directional
effects for different components of ﬂow and fund returns.
Lou (2012) shows that the expected part of ﬂow-induced
trading  positively  forecasts  mutual  fund  returns  in  the
following  year.  Song  (2020)  ﬁnds  that  fund  ﬂows  asso-
ciated  with  positive  factor  related  returns  lead  to  nega-
tive  future  fund  performance.  Our  machine  learning  ap-
proach revives the predictive role of ﬂows, with a 4-factor
risk-adjustment, and shows that fund ﬂow predicts perfor-
mance positively.

Carhart (1997) ﬁnds that persistence in fund net perfor-
mance essentially disappears once a stock momentum fac-
tor is added, apart for the worst performing funds where
it arises from persistently high expenses. With the aid of
machine learning, we identify an important predictive role
for fund past performance both gross and net of fees, even
after  controlling  for  stock  momentum.  Furthermore,  the
predictive power of our method is long lived. Bollen and
Jeffrey  (2005)  argue  that  part  of  the  reason  for  the  lack
of  performance  persistence  in  Carhart  (1997)  is  that  he
forms  decile  portfolios  and  considers  the  time  series  of
performance of these decile portfolios, instead of comput-
ing  an  abnormal  return  at  the  stock  level  and  averaging
that across stocks in each subsequent period. Our predic-
tive  results,  which  ﬁnd  an  important  role  for  fund  past
performance, hold for long-short portfolios as well, high-
lighting that including fund past performance as part of a
neural network prediction model is important.

Our paper more broadly relates to the fund return pre-
dictability literature. Cremers and Petajisto (2009) ’s Active
Share—funds  with  holdings  that  differ  greatly  from  their
benchmarks—predicts  benchmark  index-adjusted  Carhart
alphas. Kacperczyk et al. (2008) ’s Return Gap predicts 4-
factor  monthly  alphas.  The  monthly  abnormal  return  we
identify is about twice as large as theirs. While they ﬁnds
signiﬁcance for the short but not the long leg, we ﬁnd sig-
niﬁcance  for  both. 2  More  importantly,  we  show  that  the
predictive power of fund momentum and fund ﬂows are
substantially ampliﬁed when investor sentiment is high at
the time of forming portfolios.

There  is  fairly  little  evidence  on  the  impact
of  macro-economic
performance.
conditions
Moskowitz  (20 0 0)  and  Kosowski  (2011)  ﬁnd  that  risk-
adjusted  performance  of  mutual  funds  is  better  in  re-

on

2

Some other predictive variables identiﬁed in the literature include, for
example, Industry Concentration of holdings ( Kacperczyk et al., 2005 ) and
fund R 2

( Amihud and Ruslan, 2013 ).

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

cessions  than  in  booms.  Massa  and  Yadav  (2015)  show
that  a  fund’s  level  of  exposure  to  high-sentiment  beta
stocks  predicts  lower  future  returns.  Sentiment  affects
the  out-performance  of  fund  managers  differently  than
long-short  anomaly  strategies.  Similar  to  the  ﬁndings  in
Stambaugh  et  al.  (2012)  for  stock  return  anomalies,  we
ﬁnd that high sentiment periods coincide with more fund
return predictability. While the effect for equity anomalies
comes  primarily  from  its  short  leg,  the  out-  respectively
under-performance of the best and worst fund managers
in  high  sentiment  periods  is  symmetric,  suggesting  a
different economic channel. In contrast to the novel inter-
action effects between sentiment and fund characteristics,
we ﬁnd no equivalent interaction effects with the state of
the macro-economy as proxied by CFNAI.

Our  work  connects  to  the  growing  Machine  Learning
(ML) literature in ﬁnance (see Karolyi and Van Nieuwer-
burgh,  2020 ,  for  a  summary).  This  literature  has  fo-
cused on analyzing the cross-section of stock returns us-
ing  a  plethora  of  return  predictors. 3  Similar  techniques
are  beginning  to  be  used  in  other  asset  classes. 4  In-
dependent  work  to  ours  by  Li  and  Rossi  (2021)  and
DeMiguel  et  al.  (2023)  study  mutual  fund  performance
with ML techniques, providing a comparison study of pre-
dicting fund returns or abnormal returns, respectively, with
machine  learning  methods  similar  to  Gu  et  al.  (2020) .
In  addition  to  our  methodological  innovations,  we  use
a  richer  information  set,  which  allows  us  to  disentan-
gle  the  relative  value  of  holdings-based,  fund-speciﬁc,
and  macroeconomic  information.  In  addition,  Li  and
Rossi (2021) predict fund total returns using holding-based
stock  characteristics.  We  conﬁrm  and  reﬁne  their  analy-
sis  by  showing  that  holdings-based  stock  characteristics
only  predict  the  systematic  component  of  fund  returns.
Our  main  object  of  interest  is  the  fund  abnormal  re-
turn, which is orthogonal to the systematic component of
fund returns. 5  These abnormal returns are only predicted
by  fund-speciﬁc  characteristics  and  sentiment,  and  not
by stock-speciﬁc characteristics. In contemporaneous work,
DeMiguel et al. (2023) also predicts abnormal returns, but
uses only fund-speciﬁc characteristics without macroeco-
nomic information. In order to capture how a model can
change depending on macroeconomic conditions, it is nec-
essary to also include the macroeconomic variables as pre-
dictors. 6 Furthermore, neither paper includes price trends

3

4

5

6

Recent contributions include among others: return prediction with
ﬂexible  and  regularized  models  in  Freyberger  et  al.  (2020)  and
Gu  et  al.  (2020) ,  robust  stochastic  discount  factor  construction  with
many  characteristics  in  Kozak  et  al.  (2020) ,  Chen  et  al.  (2023) ,
Bryzgalova et al. (2021) and Cong et al. (2022) and estimation and eval-
uation of risk factors in Lettau and Pelger (2020) , Kelly et al. (2019) , and
Feng et al. (2020) .

Bianchi et al. (2021b,a) study bonds, Filippou et al. (2022) currencies,

and Wu et al. (2021) hedge fund strategies

A two-step procedure that predicts total, rather than abnormal, fund
returns in a ﬁrst step and then estimates a four-factor model on ex-post
prediction-based return portfolios to form abnormal returns in the sec-
ond step is fundamentally different from our procedure which directly
predicts abnormal returns.

An ex-post regression on sentiment or sentiment indicators is not suf-
ﬁcient to detect the interaction effects with sentiment our ML method
uncovers. We show that the overall model changes depending on inter-

of fund returns as predictors, which we ﬁnd to be the most
relevant.  In  summary,  our  results  emphasize  the  role  of
fund-speciﬁc  characteristics  and  the  interaction  with  the
state of the economy, thereby making progress on under-
standing the economic mechanism.

The  rest  of  the  paper  is  organized  as  follows.
Section 2 describes our data. Section 3 describes our neu-
ral  network  model  and  our  main  results.  Section  4  ana-
lyzes the main results in depth. Section 5 concludes. The
appendix provides additional empirical results (A), imple-
mentation details (B), and statistical signiﬁcance tests (C).
An Internet Appendix contains auxiliary results.

## 2. Data

### 2.1. Mutual funds

As is customary, we focus on actively-managed mutual
funds holding mostly domestic equities. The mutual fund
returns, expenses, total net assets (TNA), investment objec-
tives and other fund characteristics are from the Center for
Research in Security Prices (CRSP) Survivor Bias-Free Mu-
tual  Fund  Database.  Our  analysis  requires  fund  holdings,
which we obtain by linking the database to the Thomson
Financial Mutual Fund Holdings. Our cleaned data set in-
cludes  407,158  (mutual  fund  by  month)  observations  for
3275 mutual funds spanning the period from January 1980
until January 2019. We restrict our study to mutual funds
with raw returns observed at time t and holdings data and
total  net  assets  observed  at t − 1 ,  which  guarantees  that
holding-based  abnormal  return  returns  at  time t,  as  de-
ﬁned  below,  are  observed.  At  each  time t,  mutual  funds
are also required to have at least 30 non-missing return
observations in the last 36 months, which guarantees that
the  regression-based  abnormal  returns  are  well-deﬁned.
Internet Appendix IA.1 contains more details and summary
statistics.

### 2.2. Abnormal fund returns

Our  main  object  of  interest  is  the  abnormal  mutual
fund return. It measures fund performance after subtract-
ing compensation for systematic risk factor exposure. We
construct  the  abnormal  return  for  each  fund-month  ob-
servation relative to the Carhart (1997) model, following a
similar procedure. First, factor loadings are estimated over
the prior 36 months:
R i,t −36: t −1 = αi + F t −36: t −1 ˆ βi,t−1 + ηi, −36: t−1 ,

(1)

where  R
i,t  is  the  gross  (before-fee)  return  of  fund  i  in
month t in excess of a one-month T-bill yield. The rolling
window  regressions  allow  for  time-varying  factor  expo-
sures. Second, abnormal returns ( R abn

i,t  ) are computed:

i,t  = R i,t − F t ˆ βi,t−1 .
R abn
Abnormal  returns  are  not  guaranteed  have  a  mean  of
zero. Their mean and median is −0.03% per month in our

(2)

actions of fund-level variables with sentiment and not just an additive
sentiment component.

97

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

sample  with  a  standard  deviation  of  2.00%.  Hence,  mu-
tual  funds  earn  returns  commensurate  with  the  predic-
tions of the Carhart model on average, but with substantial
cross-sectional dispersion. While there is some controversy
over which return model actual mutual fund investors use
( Berk  and  Van  Binsbergen,  2015;  Barber  et  al.,  2016;  Je-
gadeesh and Mangipudi, 2021 ), the Carhart model arguably
remains the main factor model in the mutual fund litera-
ture and hence a natural benchmark for our purposes. The
main results are robust to using abnormal returns with re-
spect to an eight-factor model. 7

We  will  use  machine-learning  techniques  to  connect
abnormal  fund  returns  to  the  characteristics  of  mutual
funds, including the characteristics of the stocks they hold,
and to variables that capture the state of the economy.

### 2.3. Holdings-based characteristics

Mutual funds hold stocks. The stock characteristics are
from Chen et al. (2023) and cover 46 characteristics that
have been shown to have predictive power for the cross-
section of expected returns. They are listed in Table 1 in
six subgroups.

There are 332,294 fund-by-time observations with fully
observed fund characteristics. We impute the missing fund
characteristics with a latent factor model in the character-
istics space as described in A.1. Hence, we have a complete
set of fund characteristics for all 407,158 fund-by-time ob-
servations. Our results are robust to the data imputation
and are essentially identical on the subset of funds with
fully observed data.

All  stock  characteristics  are  cross-sectionally  normal-
ized to range from −0.5 to 0.5 based on stocks’ rankings
on that characteristic. We normalize the sign of the char-
acteristic  ranking  of  stocks  such  that  the  corresponding
long-short factor has a positive risk premium. For exam-
ple for size (LME), the largest stocks have negative rank-
ings while small stocks have positive rankings. The stock-
speciﬁc  characteristics  of  each  fund  are  weighted  by  the
fund’s holdings.

### 2.4. Fund and family characteristics

In addition to the 46 stock characteristics, we also form
13 fund characteristics sorted in the last three subgroups
shown in Table 1 : fund momentum, fund characteristics,
and fund family characteristics. The three fund momentum
characteristics are computed from fund abnormal returns
as deﬁned in Table 2 . Fund momentum is different from
holdings-based stock momentum. First, portfolio holdings
information  is  only  available  quarterly,  while  funds  also
trade  within  the  quarters.  Hence,  holdings-weighted  av-
erages of stock momentum, which use quarterly-updated
weights for monthly-updated stock quantiles, can only pro-
vide an approximation. Second, fund momentum is based
on the time series of residuals after removing the correla-
tion with a stock market-based momentum factor.

7

That  model  includes  market,  size,  value,  momentum,  investment,
proﬁtability, short-term reversal, and long-term reversal factors. The re-
sults are available upon request.

Following Brown and Wu (2016) , fund family is iden-
tiﬁed  by  the  management  company  code.  The  variables
“Family_r12_2” and  “Family  ﬂow” are  the  average  of  the
fund-level counterparts, “F_r12_2” and “ﬂow,” weighted by
TNA of all funds in the family, excluding the fund itself.
“Family age” is the age of the oldest fund in the family, ex-
cluding the fund itself. “Fund no” is the number of funds
in the family and “Family tna” is the sum of TNAs of all
funds in the family excluding the fund itself. The fund and
family characteristics are similarly normalized.

On average, mutual funds in our sample are 13.7 years
old,  manage  $1153  million  dollars  in  assets,  and  charge
a monthly expense ratio of around 0.1%. The fund’s ﬂow
i,t −T NA
T NA

is deﬁned as  f low

. Throughout the

i,t =

i,t−1 (1+ R
i,t−1

T NA

i,t )

sample period the mutual fund industry is growing; on av-
erage funds enjoy a 1.6% monthly inﬂow.

### 2.5. Macro-economic information

To  study  whether  fund  performance  can  be  linked  to
the state of the economy, we include investor sentiment
( Baker and Wurgler, 2006 ) and the Chicago Fed National
Activity Index (CFNAI), a series which captures the state of
the macro economy and is itself an index of many macro
time  series. 8  Fig.  1  plots  the  time  series  plots  of  both
macro variables. Kacperczyk et al. (2014) shows that mu-
tual fund performance depends on CFNAI.

## 3. Main analysis

Our  main  analysis  aims  to  predict  mutual  fund  ab-
normal returns. This analysis is an out-of-sample predic-
tion  analysis  with  many  conditioning  variables.  It  allows
for  interactions  of  characteristics  (the  59  characteristics
in  Table  1  plus  sentiment/CFNAI),  as  well  as  for  non-
linearities in the relationship between characteristics and
future fund outperformance. To that end, we use an arti-
ﬁcial neural network, similar to Gu et al. (2020) . In their
extensive comparison study, they show that this method
dominates  other  ML  techniques  for  predicting  stock  re-
turns. We predict fund abnormal returns with a neural net-
work of lagged predictors:
i,t+1 = g(z it , z t ) + (cid:5)i,t+1
R abn
The structure of the neural network g(·) is selected based
on a validation sample. It uses as its inputs the characteris-
tics z
i,t speciﬁc to mutual funds, and macro-economic vari-
ables z t  to build the best predictors of fund abnormal re-
turns. We focus on sentiment as our main macroeconomic
variable, and discuss the results with CFNAI as a robustness
check.

(3)

8

CFNAI is the ﬁrst principal component of 85 economic indicators
from four broad categories: production and income; employment, unem-
ployment, and hours; personal consumption and housing; and sales, or-
ders, and inventories. Sentiment also uses principal component analysis
to combine the information from multiple economic indicators, which in-
clude the closed-end fund discount, NYSE share turnover, number of IPOs,
average ﬁrst-day returns on IPOs, equity share in new shares and the div-
idend premium.

98

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 1
Fund-speciﬁc and stock-speciﬁc characteristics by category.

Past Returns

(30)

CF2P

Cashﬂow to price

(1)
(2)
(3)
(4)
(5)
(6)

(7)
(8)
(9)

r2_1
r12_2
r12_7
r36_13
ST_Rev
LT_Rev

Short-term momentum
Momentum
Intermediate momentum
Long-term momentum
Short-term reversal
Long-term reversal

Investment

Investment
NOA
DPI2A

(10)  NI

Proﬁtability

PROF
ATO
CTO
FC2Y

(11)
(12)
(13)
(14)
(15)  OP

(16)
(17)
(18)
(19)
(20)

PM
RNA
ROA
ROE
SGA2S

(21)  D2A

Investment
Net operating assets
Change in property, plants, and
equipment
Net Share Issues

Proﬁtability
Net sales over lagged net operating assets
Capital turnover
Fixed costs to sales
Operating proﬁtability

Proﬁt margin
Return on net operating assets
Return on assets
Return on equity
Selling, general and administrative

expenses to sales
Capital intensity

Intangibles

(22)
AC
(23)  OA
(24)  OL

Accrual
Operating accruals
Operating leverage

(25)

PCM

Price to cost margin

Value

A2ME
BEME
C
CF

(26)
(27)
(28)
(29)

Assets to market cap
Book to Market Ratio
Ratio of cash and short-term
Free Cash Flow to Book Value

(31)  D2P
(32)
E2P
(33)  Q
(34)
(35)

S2P
Lev

Dividend Yield
Earnings to price
Tobin’s Q
Sales to price
Leverage

Trading Frictions

(36)

AT

Total Assets

Beta
IdioVol
LME
LTurnover

(37)
(38)
(39)
(40)
(41)  MktBeta
Rel2High
(42)
Resid_Var
(43)

(44)
(45)
(46)

Spread
SUV
Variance

CAPM Beta
Idiosyncratic volatility
Size
Turnover
Market Beta
Closeness to past year high
Residual Variance

Bid-ask spread
Standard unexplained volume
Variance

Fund Momentum

(47)
(48)
(49)

F_ST_Rev
F_r2_1
F_r12_2

Fund short-term reversal
Fund short-term momentum
Fund momentum

Fund Characteristics

(50)
(51)
(52)
(53)

age
tna
ﬂow
exp_ratio

Fund age
Fund tna
Fund ﬂow
fund expense ratio

(54)

turnover ratio

turnover ratio

Fund Family Characteristics

family_tna
fund_no
Family_r12_2

family tna
number of funds in family
family momentum

Family_age
Family_ﬂow

Family age
Family ﬂow

(55)
(56)
(57)

(58)
(59)

This table shows all 59 characteristics sorted into nine categories. The ﬁrst six categories represent stock-speciﬁc characteristics and the
last three characteristic groups are fund-speciﬁc characteristics.

Table 2
Fund momentum characteristics.

Acronym

Name

Deﬁnition

F_r2_1
F_r12_2

Short-term momentum
Momentum

F_ST_Rev

Short-term reversal

Lagged one-month abnormal return
Mean abnormal return from past 12 months before the
abnormal return prediction to two months before. Need
at least 8 non-missing samples to be included.
Prior month abnormal return

Reference

Jegadeesh and Titman (1993)
Fama and French (1996)

Jegadeesh and Titman (1993)

This table summarizes the fund momentum characteristics. We use a ‘F’ preﬁx to denote that these characteristics are based on mutual
funds. It includes their acronym, name, deﬁnition and reference of their stock based counterpart. The fund momentum characteristics
follow the same deﬁnition as their stock counterpart in Chen et al. (2023) .

### 3.1. Sampling scheme

We use a cross-out-of-sample analysis to evaluate the
performance of the neural network model. We split the full
sample into three folds, periods of the same length. We use
two of the folds to estimate the model and select the tun-

ing parameters, and evaluate the prediction out-of-sample
on  the  remaining  fold.  Following  Kozak  et  al.  (2020) ,
Lettau  and  Pelger  (2020)  and  Bryzgalova  et  al.  (2021) ,
we cross-validate the estimation on three different com-
binations  of  the  three  folds,  thereby  obtaining  an  out-
of-sample  prediction  for  each  data  point  in  our  sam-

99

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 1.  These ﬁgures show the macroeconomic time series plot. Panel (a) plots the sentiment time series and panel (b) plots the CFNAI time series.

ple. This cross-out-of-sample evaluation diminishes the ef-
fect  of  particular  subperiods  in  the  out-of-sample  anal-
ysis.  The  estimation  and  validation  time  period  (2/3  of
the  sample)  is  split  into  3/4  used  for  estimation  (train-
ing)  and  1/4  used  for  validation  (to  select  the  tuning
parameters).

Our baseline results select the dates that go into each
of the three folds randomly. The top panel of Fig. 2 shows
this random sampling scheme, where different colors de-
note  the  three  folds.  The  bottom  panel  shows  the  more
traditional chronological sampling. A second alternative is
an expanding-window chronological estimation and eval-
uation  without  cross-validation.  We  analyze  the  two  al-
ternative  sampling  schemes  below,  and  show  that  our
benchmark predictability results are robust to the sampling
scheme. 9

Each sampling scheme has beneﬁts and drawbacks. The
random  sampling  approach  has  the  important  advantage
of  having  a  more  equal  distribution  of  high-  and  low-
sentiment observations in each fold, as illustrated in Fig. 2 .
In contrast, the chronological sampling approach may have
no  high-sentiment  periods  in  the  evaluation  fold  (in  the
validation where the green fold is used for out-of-sample
evaluation) or the estimation fold (in the validation where
the green fold is used for estimation). If sentiment is an
important conditioning variable in the prediction problem,

9

In Internet Appendix IA.3, we also investigate the impact of overlap
between data points that are both in the 36-month window used for the
estimation of the abnormal return ( Eqs. (1) and (2) ) and in the testing
fold in the random cross-out-of-sample validation. We ﬁnd that eliminat-
ing this overlap has minimal impact on the results, but reduces estima-
tion precision.

as we will show is the case, the chronological results will
fail to accurately capture the dependencies on the underly-
ing economic state. By using the full time span of the data,
the random sampling scheme allows the model to better
learn the non-linear function g(z

it , z t ) .

The  random  sampling  scheme  does  not  create  look-
ahead  bias.  The  economic  object  of  interest  is  the  con-
it , z t ) .  A  prediction  can  be
ditional  abnormal  return  g(z
interpreted  as  a  cross-sectional  non-parametric  regres-
sion, where the time-series order of the cross-sectionally
stacked triplets { R abn
i,t  is not explicitly taken into
i,t+1
account. This regression only uses variables known at time
t to predict abnormal returns at time t + 1 . Information in
the error term (cid:5)t+1 of the prediction is never used in the
prediction.

it , z t }

, z

What is true is that both the random and chronologi-
cal sampling schemes with cross-validation are not avail-
able to investors in real-time. In contrast, the expanding-
window chronological sampling scheme does represent a
feasible investment strategy at each date. However, the lat-
ter estimates a new model at each point in time, making
the interpretation more problematic. It also uses less data
for evaluation and estimation, sacriﬁcing precision. Because
it uses less data and because is not a cross-validation, it
has  an  even  less  representative  distribution  of  economic
states to learn from at each date.

### 3.2. Neural network

A  feedforward  network  (FFN)  is  a  ﬂexible  non-
parametric  estimator  that  can  learn  any  functional  rela-
tionship y = f (x ) between an input x and output variable

100

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 2.  This ﬁgure plots the Baker and Wurgler (2006) sentiment measure from 1979/12 to 2018/12. Different colors denote the three different cross-out-of-
sample folds, which we use throughout the paper. The top ﬁgure shows the random sampling into three folds, while the bottom ﬁgure shows chronological
sampling.

Fig. 3.  Illustration of Feedforward Network with Single Hidden Layer.

y with suﬃcient data. 10 A deep neural network combines
several layers by using the output of one hidden layer as

FFN are among the simplest neural networks and treated in detail in

10
standard machine learning textbooks, e.g. Goodfellow et al. (2016) .

101

an input to the next hidden layer. Our best model struc-
ture is a one-layer neural network.

It  combines  the  raw  predictor  variables  (or  features)
z = z (0) ∈ R K (0)
linearly  and  applies  a  non-linear  trans-
formation. This non-linear transformation is based on an
element-wise operating activation function. We choose the

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 4.  These ﬁgures show the equal and prediction-weighted portfolio weights for the ﬁrst and tenth decile in a long-short portfolio for the representative
example month 20 0 0/01. The x -axis refers to the sorted ﬁrms in the bottom 10% and in the top 10% of the predicted abnormal return distribution.

popular  rectiﬁed  linear  unit  activation  function  (ReLU), 11
which  component-wise  thresholds  the  inputs  and  is  de-
ﬁned as:

ReLU (z

k ) = max (z

k , 0) .

(1)
The result is the hidden layer z (1) = (z
K (1) ) of di-
mension  K (1)  which  depends  on  the  parameters W (0) =
(0)
(w
0  . The output layer
is simply a linear transformation of the output from the
hidden layer ( Fig. 3 ).

(0)
K (0) ) and the bias term w

(0)
1  , . . . , w

(1)
1  , . . . , z

(1) = ReLU ( W
z
(cid:2)

(0) (cid:4)

(0)
0  )

(0) + w
z
K (0) (cid:3)

(cid:4)

= ReLU

w

(0)
0  +

w

(0)
(0)
k  z
k

R abn = W

(1) (cid:4)

k =1
(1)
(1) + w
z
0
(1) ∈ R K (1)

with z

, W

(0) ∈ R K (1) ×K (0)

, W

(1) ∈ R K (1)
.

Note  that  without  the  non-linearity  in  the  hidden  layer,
the one-layer network would reduce to a generalized lin-
ear model. Our optimal network has 64 nodes in the hid-
den layer, which can be interpreted as representing the in-
formation set with 64 basis functions which are non-linear
transformations of the original characteristics and macroe-
conomic variables and which are linearly combined to pre-
dict the abnormal return.

Our results are extremely robust to the choice of tun-
ing parameters. Networks with more layers and nodes re-
sult  in  a  very  similar  performance  and  estimated  func-
tional form as our optimal network. This is consistent with
the  ﬁndings  in  Chen  et  al.  (2023)  and  Gu  et  al.  (2020) .
Hence, it matters primarily to allow for the ﬂexible func-
tional form and interaction effects, which can be achieved
with many model speciﬁcations. The details of the hyper-
parameter tuning are in Appendix B , where we also show

11
ReLU activation functions have a number of advantages including the
non-saturation of its gradient, which greatly accelerates the convergence
of stochastic gradient descent compared to the sigmoid/hyperbolic func-
tions and fast calculations of expensive operations.

the robustness to the number of layers in Section IA.4 of
the Internet Appendix.

We quantify the economic beneﬁt of different informa-
tion sets by comparing the prediction and trading beneﬁts
of each information set available to the neural network. As
appropriately tuned neural networks can approximate any
functional relationship, they allow us to understand what
the best possible prediction is for a given information set.
As  a  robustness  check,  we  explore  Gradient  Boosted
Trees as an alternative machine learning approach. We ob-
tain broadly similar conclusions, and relegate an in-depth
comparison  to  Internet  Appendix  IA.5.  Neural  networks
have the advantage that we can provide valid conﬁdence
intervals,  similar  to  regression  analysis,  which  is  not  al-
ways the case for alternative machine learning predictors.

### 3.3. Optimal prediction

Having estimated the neural network model, we form
the  model’s  prediction  of  fund  abnormal  returns  for
each  fund-month  using  all  59  characteristics  listed  in
Table 1 and investor sentiment. We sort funds in deciles
based  on  their  predicted  abnormal  return  for  the  next
month.

Within  the  deciles  we  weight  the  funds  either  by
their predicted value or equally. Fig. 4 illustrates the two
weighting schemes in the extreme deciles for a representa-
tive month. The prediction weights in the left panel exploit
the  heterogeneity  in  the  prediction  and  assign  a  higher
relative weight to predictions that deviate more from the
center of the decile. 12

The prediction based weights are deﬁned as the following shifted and

12
scaled weights:
For top portfolio:  ˜ μi,t = ˆ μi,t − min
i ∈ Top

( ˆ μi,t )

For bottom portfolio:  ˜ μi,t = ˆ μi,t − max
i ∈ Bottom

( ˆ μi,t )

w pred
i,t  =

˜ μi,t
(cid:5)
N
i =1 ˜ μi,t

102

(4)

(5)

(6)

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 5.  These ﬁgures show the cumulative abnormal returns sorted into prediction deciles when considering the complete information set (fund-speciﬁc
and stock-speciﬁc characteristics + sentiment) to predict abnormal returns.

Fig.  5  plots  the  cumulative  abnormal  return  from  in-
vesting  in  each  of  these  10%  of  funds.  The  right  panel
equally-weights the abnormal returns of the funds within
each decile, using the neural network model only to sort
funds into deciles. The left panel additionally uses the neu-
ral  network  model  prediction  to  form  portfolio  weights;
we  refer  to  this  as  the  prediction-weighted  return.  A
prediction-weighted  approach  uses  more  information  re-
sulting in a larger spread in the prediction portfolios. The
baseline  model  for  the  rest  of  the  paper  is  prediction-
weighted. 13  An investor who had followed an investment
strategy that invests in the 10% best mutual funds based on
the neural network model’s predictions would have earned
a cumulative abnormal return of 72% prediction-weighted
and  48%  equally-weighted.  The  difference  between  these
two numbers shows that the neural net is not only good
at predicting which funds are likely to be in the top per-
formance decile, but also at how good some of the funds in
the top decile are relative to other top-performing funds.

At the other end of the spectrum, the 10% worst funds
according  to  the  out-of-sample  prediction  of  the  neural
network  model  generate  cumulative  abnormal  returns  of
−119%  prediction-weighted  and  −93%  equally-weighted.
Hence, avoiding the 10% worst mutual funds is even more
valuable than investing in the best 10% of mutual funds.

The  main  conclusion  is  that  abnormal  mutual  fund
returns  are  predictable  and  the  extent  of  predictability

where  ˆ μi,t  are  the  predictions  of  neural  network  models.  For  top-
performing funds, we subtract the smallest model prediction within the
group in Eq. (4) to ensure that the top portfolio is a long-only portfolio.
For bottom-performing funds, we subtract the largest model prediction
within the group in Eq. (5) to ensure that the bottom portfolio is a short-
only portfolio. We then standardize the normalized predictions to sum up
to 1 per Eq. (6) . The prediction weights are similar for the other deciles.
The results for quintiles and 20 quantiles are very similar and available
upon request. An alternative to the prediction weights within the quan-
tiles are rank weights. The results with rank weights are very similar to
those with prediction weights and are omitted for brevity.
13
The results for the equally-weighted approach are similar and pre-
sented in Appendix A.1.3 . We explore a third weighting scheme, which is
value-weighted returns in Appendix A.1.8 .

over  the  past  40  years  is  economically  large.  The  cu-
mulative  abnormal  return  translates  into  a  monthly  out-
performance  of  15  basis  points  for  the  10%  best  funds
prediction-weighted  (10  basis  points  equally-weighted).
The 10% worst funds see 25 basis point per month under-
performance prediction-weighted (20 basis points equally-
weighted).

Panel  (a)  of  Fig.  6  shows  the  average  fees  for  the
different  prediction-based  decile  portfolios.  While  those
funds with higher predicted and realized abnormal returns
charge a higher fee, the spread in fees does not explain the
spread in expected returns. In fact, the worst and best 10%
of funds both have a cumulative expense ratio of around
50%, which are higher than the expense ratios of the funds
in  the  middle  of  the  predicted  performance  distribution.
Given  that  the  10%  best  and  10%  worst  funds  have  the
same fees, fees can explain nothing of their relative perfor-
mance. The 10% best funds earn cumulative abnormal gross
returns  of  72%,  exceeding  cumulative  fees.  Indeed,  Panel
(b) of Fig. 6 shows that the funds in the top two predic-
tion deciles still earn a positive abnormal return after fees.
Note that these are lower bounds as predicting abnormal
returns  after  fees  (rather  than  before  fees)  improves  the
predicted after-fee performance. Fig. A.1 shows the perfor-
mance for predicting abnormal after-fee returns. The 10%
best funds achieve a cumulative abnormal return after fees
of 37%, which substantially exceeds the 72% gross outper-
formance minus 50% in fees. On the other hand, the 10%
worst funds earn cumulative abnormal returns after fees
of around −170%, further highlighting the usefulness of the
neural network in identifying which funds to avoid.

In the frictionless Berk and Green (2004) model, all the
out-performance should  go  to  the  managers in  the  form
of higher fee revenues, resulting in zero abnormal returns
after  fees.  Rather,  we  ﬁnd  that  about  20%  of  funds  out-
perform  after  fees,  while  the  remaining  80%  have  nega-
tive  after-fee  performance.  The  outperformance  suggests
the  presence  of  frictions,  while  the  underperformance  is
consistent with the presence of unsophisticated investors
that do not account properly for risk after fees and neglect

103

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 6.  The left ﬁgure shows the cumulative expense ratios of prediction-weighted deciles based on the full information set (fund-speciﬁc and stock-speciﬁc
characteristics + sentiment). The right ﬁgures shows the abnormal net returns for the prediction-weighted deciles, that is, the abnormal returns minus the
fees.

to withdraw their investments ( Ben-David et al., 2022 ). The
asymmetry seems to support a separation of investors into
ǣsmart ǥ and ǣunsophisticated ǥ investors.  The  best funds
charge  among  the  highest  fees,  in  line  with  the  predic-
tions of Berk and Green (2004) . However, unsophisticated
investors do not properly measure skill and end up invest-
ing into funds  that  earn negative abnormal returns  after
fees.

The magnitude of the predictability deserves some dis-
cussion. First, the measured performance is not the alpha
of a trading strategy, but the realized performance of mu-
tual  funds.  Second,  it  refers  to  an  abnormal  return  be-
yond  the  compensation  for  exposure  to  the  four  factors.
Most,  importantly,  it  represents  an  out-of-sample  perfor-
mance. Related work by Roussanov et al. (2021, 2022) uses
Bayesian  forecasts  of  after-fee  outperformance  that  are
based  on  deviations  of  fund  size  relative  to  what  the
Berk and Green (2004) model implies. They obtain magni-
tudes in performance comparable to ours, but their results
are  not  entirely  out-of-sample.  Hence,  our  out-of-sample
predictability of 15 basis points monthly for the top funds
and  -25  basis  points  for  the  worst  funds  over  a  40-year
sample is substantial. 14

### 3.4. Which information most useful when predicting fund abnormal returns?

To assess the importance of stock-speciﬁc characteris-
tics  (labeled  1–46  in  Table  1 ),  fund  momentum  (47–49),
fund characteristics (50–54), family characteristics (55–59),
and sentiment for the prediction of fund abnormal perfor-
mance, we estimate neural network models that are given

14
Roussanov et al. (2021) show in their Fig. 2 that the top predicted-
skill decile outperforms by 5.8 basis points monthly and the bottom
decile underperforms by 23 basis points. Roussanov et al. (2022) show
in their Table 4 that the top (bottom) decile has a performance of 11 ba-
sis points ( −26 basis points) value weighted. Similar to our results, only
the top decile has a signiﬁcantly positive net-of-fee alpha. Overall, their
results provide a useful benchmark to compare to for our out-of-sample
analysis.

subsets  of  predictors.  Our  main  ﬁnding  is  that  the  com-
bination  of  fund-level  variables  and  sentiment  results  in
the best performance. Stock-speciﬁc characteristics of the
stocks held by funds do not help predict fund abnormal
return.

Fig.  7  shows  the  cumulative  abnormal  returns  for
the  fund  deciles  when  using  stock  characteristics  1–46
only (Panel A), stock characteristics and sentiment (Panel
B),  fund  characteristics  47–59  (Panel  C),  and  fund  char-
acteristics  and  sentiment  (Panel  D).  Fund  abnormal  re-
turns within each decile are prediction-weighted. The best
model for predicting fund abnormal returns ignores stock
characteristics entirely. Fund characteristics, in sharp con-
trast to stock characteristics, are extremely useful for pre-
diction, as is sentiment. We note the monotone pattern in
Panel D. As we will see shortly, fund characteristics inter-
act with sentiment in important ways.

As most of the predictability is in the extreme deciles,
we propose a long-short prediction portfolio of the top and
bottom decile as a measure for the spread in skill. This is
a convenient economic measure of the spread, not a trad-
able  investment  strategy.  Fig.  8  shows  that  the  portfolio
that  goes  long  in  the  (predicted)  best  10%  of  funds  and
short in the (predicted) worst 10% of funds earns cumu-
lative returns of -9% out-of-sample when only stock infor-
mation is used, 69% when using stock plus sentiment in-
formation, 178% when using fund information, 188% when
using fund plus sentiment information, and 191% when us-
ing stock plus fund plus sentiment information. The results
are qualitatively the same for equally-weighted portfolios
as shown in Appendix A.1.3 .

To  assess  whether  these  different  long-short  invest-
ment strategies incur different amounts of risk, we com-
pute  the  Sharpe  Ratio  on  the  long-short  decile  portfo-
lio, which Table 3 reports alongside the mean return. The
highest  Sharpe-ratio  strategy  ignores  stock-speciﬁc  infor-
mation.  Using  fund  information  and  sentiment  to  select
the best and worst 10% of funds results in a monthly long-
short return of 40 basis points with a monthly Sharpe ratio
of 0.25, which translates into a 0.87 annual Sharpe ratio.

104

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 7.  These ﬁgures show the cumulative abnormal returns sorted into prediction deciles for different information sets. The returns are prediction-
weighted within deciles. We consider fund-speciﬁc characteristics + sentiment, stock-speciﬁc characteristics+ sentiment, fund-speciﬁc characteristics or
stock-speciﬁc characteristics to predict abnormal returns.

Fig. 8.  This ﬁgure plots the cumulative abnormal returns of prediction-weighted long-short decile portfolios that use different information sets for predic-
tion. We consider fund-speciﬁc and stock-speciﬁc characteristics combined with sentiment.

105

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 3
Performance of long-short abnormal return portfolios for different information sets.

Information set  mean(%)

t-stat

Stock + fund + sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Fund momentum + sentiment
Fund momentum + Flow + sentiment
Fund excl. fund momentum and ﬂow

0 .41
0 .40
0 .38
0 .28
0 .15
−0 .02

0 .35
0 .48
0 .06

4 .5 ∗ ∗ ∗
5 .4 ∗ ∗ ∗
5 .5 ∗ ∗ ∗
3 .3 ∗ ∗ ∗
1 .6
−0 .2

4 .4 ∗ ∗ ∗
5 .2 ∗ ∗ ∗
1 .5

SR

R 2
F (%)
5 .00
2 .73
0 .19
2 .30
1 .27
−0 .01  −1 .60

0 .21
0 .25
0 .25
0 .15
0 .07

0 .21
0 .24
0 .07

0 .29
0 .92
0 .12

This table reports the Sharpe ratio, mean and factor R 2
of long-short prediction-
weighted decile portfolios that use different information sets for the prediction. We
consider nine different information sets which combine fund-speciﬁc and stock-speciﬁc
characteristics and sentiment. We also include ﬂow and fund momentum (F_r12_2,
F_r2_1 and F_ST_Rev) individually.

The last three rows show that when one only uses four
out  of  the  13  fund  characteristics,  namely  the  fund  mo-
mentum group (F_r12_2, F_r2_1 and F_ST_Rev) and ﬂow,
combined with sentiment, the resulting long-short portfo-
lio has a similar mean return and Sharpe ratio to the port-
folio  based  on  all  fund  information.  The  last  row  shows
that using all fund characteristics except for these two re-
sults in substantially worse performance. In summary, fund
momentum  and  ﬂow,  interacted  with  sentiment,  are  the
key variables for predicting fund abnormal returns.
The  last  column  of  Table  3  reports  the  R 2

F  statistic,
which  measures  how  well  the  realized  long-short  port-
folio  return  is  predicted  by  the  neural  network  model. 15
If  the  realized  long-short  abnormal  return  factor  is  pre-
dicted more accurately, then an investor knows better by
how much funds in the top decile will outperform funds
in the bottom decile in the next period. 16 The highest R 2
F  of
5.00% monthly, which is substantial, is obtained for the full
model with fund, sentiment, and stock information. Drop-
ping  sentiment  information  results  in  a  large  decline  in
R 2
F , which suggests that sentiment is important for predict-
ing the high-minus-low abnormal fund return. As we will
see below, the conditional mean of the long-short portfolio
is higher in high sentiment periods. Replacing fund- with
stock-level information also results in a large drop in R 2
F .
Note  that  the  R 2
F  measures  accuracy  of  both  the  relative
cross-sectional prediction of funds (the fund ranking) and
the  level  of  the  abnormal  returns.  The  prediction  based
only on fund information correctly predicts the ranking of
future abnormal fund returns, but not their magnitude as
suggested by the low R 2
F . Including sentiment slightly im-
proves the relative prediction, due to the interaction effects
studied in Section 4.1 , but substantially improves the level
prediction of abnormal returns. 17 Table A.1 reports the re-

15
We denote by F t the realized return and by ˆ F t the predicted return of
the long-short portfolio based on prediction-sorted deciles. The normal-
ized time-series prediction error is measured by R 2
16
vestment in the spirit of Haddad et al. (2020) .
17
The results for the different measures also illustrate the challenges of
using them to select the best model. The measures are tools for under-

This information could be used for timing and sizing the portfolio in-

(cid:5)
T
t=1 ( ˆ F t −F t ) 2
(cid:5)
.
T
t=1 F 2
t

F  = 1 −

sults for the top and bottom prediction deciles separately
with the same ﬁndings.

Spanning .  Do  the  long-short  portfolio  returns  formed
from  the  neural  network  model’s  prediction  reﬂect  true
abnormal  return  or  compensation  for  risk?  To  explore
this question, we estimate a multivariate regression of the
long-short portfolio return on several sets of return factors
from the literature. The results for the main information
set is reported in the ﬁrst row of Table 4 . The second row
reports results when using fund characteristics and senti-
ment in the predictor set. In both cases, we ﬁnd large and
highly signiﬁcant intercepts α, relative to the mean return
μ (reported in the last column), and low R 2 . Hence it is
not the case that our approach results in a mutual fund
portfolio return that inadvertently captures compensation
for systematic factor exposure.

Robustness to Fund Size . The predictability is robust to
excluding  or  down-weighting  small  mutual  funds.  First,
we  exclude  mutual  funds  with  less  than  15  million  as-
set under management (TNA), which is an often used cut-
off in the literature (see for example Doshi et al., 2015 ).
Fig. 9 (b) shows the result is essentially unaffected by drop-
ping  the  smaller  funds.  Second,  we  combine  the  predic-
tion classiﬁcation with the value of the assets under man-
agement  of  the  funds  to  form  value-weighted  prediction
portfolios. Fig. 9 (a) shows that the magnitude of the out-
performance  of  the  best  over  the  worst  decile  of  funds
for value-weighted portfolios is very similar to prediction-
weighted portfolios. Interestingly, the top decile performs
better under value-weighting, suggesting that some of the
best funds have relatively high AUM. Appendix A.1.8 pro-
vides further details.

### 3.5. Longer holding periods

The  monthly  rebalancing  of  mutual  funds  is  not  cru-
cial to earning the high abnormal returns associated with
the relative performance of funds. Fig. 10 shows the abnor-
mal returns on a long-short prediction portfolio for hold-
ing periods up to 3 years. Fund investments are made ev-

standing what economic structure is captured. The models do not need
to improve uniformly along all measures.

106

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 4
Spanning of long-short abnormal prediction portfolios with different factor models.

Stock + fund+ sentiment

Fund + sentiment

Fund

Stock + fund

Stock + sentiment

Stock

Flow + fund momentum+ sentiment

F_r12_2 + sentiment

FF 4 factors
R 2

α

FF 5 factors
R 2

α

FF 6 factors
R 2

α

FF 8 factors
R 2

α

0.15 ∗ ∗ ∗
(0.04)
0.16 ∗ ∗ ∗
(0.05)
0.15 ∗ ∗ ∗
(0.05)
0.09 ∗
(0.05)
0.10 ∗ ∗
(0.04)
0.04
(0.04)

0.13 ∗ ∗ ∗
(0.04)
0.08 ∗
(0.05)

0.27

0.12

0.16

0.14

0.28

0.15

0.26

0.12

0.12 ∗ ∗ ∗
(0.04)
0.21 ∗ ∗ ∗
(0.05)
0.21 ∗ ∗ ∗
(0.05)
0.10 ∗ ∗
(0.05)
0.05
(0.04)
0.03
(0.04)

0.23 ∗ ∗ ∗
(0.04)
0.18 ∗ ∗ ∗
(0.05)

0.31

0.03

0.05

0.13

0.36

0.17

0.12

0.04

0.10 ∗ ∗
(0.04)
0.17 ∗ ∗ ∗
(0.05)
0.16 ∗ ∗ ∗
(0.05)
0.08 ∗
(0.05)
0.03
(0.04)
0.02
(0.04)

0.17 ∗ ∗ ∗
(0.04)
0.13 ∗ ∗ ∗
(0.05)

0.35

0.12

0.17

0.16

0.38

0.18

0.29

0.17

0.09 ∗ ∗
(0.04)
0.19 ∗ ∗ ∗
(0.05)
0.17 ∗ ∗ ∗
(0.05)
0.06
(0.05)
0.03
(0.04)
0.00
(0.04)

0.20 ∗ ∗ ∗
(0.04)
0.13 ∗ ∗ ∗
(0.05)

0.35

0.14

0.18

0.19

0.38

0.22

0.35

0.17

mean μ

0.15 ∗ ∗ ∗
(0.05)
0.18 ∗ ∗ ∗
(0.05)
0.19 ∗ ∗ ∗
(0.05)
0.06
(0.05)
0.09 ∗
(0.05)
0.01
(0.05)

0.17 ∗ ∗ ∗
(0.05)
0.12 ∗ ∗ ∗
(0.05)

This table reports the time-series regression results of long-short prediction-weighted decile portfolios for different factor models.
We compare different information sets to predict abnormal returns. We consider the 4-factor Fama-French-Carhart model (market,
size, value and momentum), the 5-factor Fama-French model (market, size, value, proﬁtability and investment), a 6-factor model
which adds the momentum factor to the Fama-French 5 factors, and an 8-factor model which adds the momentum, short-term
reversal and long-term reversal factors to the Fama-French 5 factors. The α column reports the time-series pricing error and R 2
is
the explained variation of the regression. Both the long-short abnormal return portfolios and the factor models are normalized to
have a standard deviation of 1. Standard errors are in brackets and stars denote the signiﬁcance levels.

Fig. 9.  These ﬁgures show the out-of-sample cumulative abnormal returns sorted into prediction deciles. We predict abnormal returns with fund-speciﬁc
characteristics and sentiment. The left subﬁgure uses prediction-value weighted portfolios, while the right subﬁgure shows the cumulative abnormal returns
for prediction-sorted portfolios for mutual funds with at least 15 million $ assets under management.

ery month based on the one-month ahead prediction, but
investments are held for a longer holding period, ranging
from 1 to 36 months (with overlapping holding periods).
As expected, the mean return decreases over time but it
stays signiﬁcant for all holding periods (top left panel). At
the  same  time,  the  longer  holding  periods  decrease  the
standard  deviation  of  the  return  (top  right  panel).  A  3-
month holding period reduces the standard deviation more
than the mean, and hence results in a higher Sharpe ratio
than the one-month holding period (bottom left). Even af-
ter 36 months, the monthly Sharpe ratio is still 0.20, com-
pared to 0.30 after 3 months. The outperformance remains
statistically signiﬁcant even after 36 months (bottom right
panel). This occurs even though the model only attempts
to predict abnormal returns one-month ahead. In light of

the literature’s diﬃculty in ﬁnding persistence in abnormal
returns, this result is remarkable.

Removing stock characteristics results in similar long-
horizon  Sharpe  Ratios  as  with  the  full  information  set.
Trading based on the most important predictors (ﬂow, fund
momentum,  and  sentiment)  results  in  similar  holding-
period patterns as using the full information set.

We  obtain  similar  results  for  longer  holding  peri-
ods  when  using  the  longer-horizon  abnormal  return  as
the prediction objective. Appendix A.1.4 shows the strong
predictability  for  an  annual  abnormal  return  prediction.
While  12-month-horizon  prediction  lowers  the  mean  re-
turn,  it  also  reduces  the  variance  and,  hence,  results  in
similar  monthly  Sharpe  ratios  as  the  one-month  ahead
prediction.

107

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 10.  This ﬁgure shows the results for long-short prediction-weighted portfolios for different holding periods. At each time t, we sort funds based on
the one-month prediction into deciles and hold the long-short prediction portfolio for s months with overlapping returns. We calculate the mean, Sharpe
ratio, standard deviation, and t-statistics of the overlapping abnormal returns. The one-month prediction uses either fund+sentiment, stock+fund+sentiment
or ﬂow+fund+sentiment.

The predictability lasts for longer because many fund-
speciﬁc characteristics contain predictive information that
remains relevant for a longer horizon. Fig. A.9 shows the
autocorrelation of fund-speciﬁc characteristics. Except for
short-term  momentum  (F_r2_1)  and  short-term  reversal
(F_ST_Rev), the fund characteristics are persistent. This is
also  reﬂected  in  the  persistence  of  the  classiﬁcation  of
funds. Fig. A.10 shows the transition matrix between the
different prediction quantiles for each month. Over 60% of
the top-20% and bottom-20% funds stay in the same pre-
diction quantile in the next month. The classiﬁcation re-
mains stable for longer time periods.

### 3.6. Sampling scheme

Results  are  not  sensitive  to  the  random  sampling
scheme with three-fold cross-validation. Appendix A.2 re-
visits all results using chronological sampling with cross-
validation, while Appendix A.3 does the same for a chrono-
logical  expanding-window  estimation.  We  highlight  the
main ﬁnding here. Panel A of Fig. 11 shows a very simi-
lar out-performance of the predicted top-decile and under-
performance of the predicted bottom decile with chrono-
logical  sampling  with  three-fold  cross-validation.  Panel

B  shows  again  similar  performance  with  chronological
expanding-window  sampling  (without  cross-validation).
Table  5  shows  that,  if  anything,  the  mean  return  and
Sharpe ratio of the long-short portfolio based on the full
information  set  are  higher  for  the  two  alternative  sam-
pling schemes than for the benchmark random sampling
scheme.

The  second  main  result,  that  stock  characteristics  are
less  useful  for  predicting  out-  and  under-performance  of
mutual funds than fund characteristics is also robust to the
sampling scheme. This is clearly visible in the right pan-
els of Fig. 11 and conﬁrmed in the row “Stock” of Table 5 .
While there is some statistical evidence for predictability
of  stock  characteristics  in  the  chronological  scheme,  the
mean return and Sharpe ratio are less than half as large as
when fund and sentiment information are added. The re-
sults in the expanding-window sampling are weaker still.

## 4. Understanding the results

### 4.1. Variable importance and interaction effects

Importance  of  Predictors .  In  order  to  visualize  which
variables are the most important for prediction, we con-

108

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 11.  These ﬁgures show the cumulative abnormal returns sorted into prediction deciles for different information sets. The abnormal returns are
prediction-weighted within deciles. We consider fund-speciﬁc characteristics + sentiment and stock-speciﬁc characteristics. In Panel A, the three cross-
out-of-sample folds keep the chronological order. In Panel B, we estimate prediction models on an expanding window, that is, for each t we use all
available data to estimate new predictions for year t + 1 . As we need an initial training data set, the out-of-sample analysis for the expanding window
starts in 1990.

struct  a  metric  based  on  the  average  squared  gradient
of  the  abnormal  return  prediction  for  each  character-
istic,  following  Sadhwani  et  al.  (2020)  and  Horel  and
Giesecke (2020) :

Sensitivity (z

k ) =

2

(7)

(cid:6)

T (cid:3)

N t (cid:3)

1
T

1
N t

t=1

i =1

(cid:8)
(cid:7) ∂ ˆ R abn
i,t+1
∂z
i,k,t

ral  network  prediction. 18  In  addition  to  the  point  esti-
mates, we can provide formal statistical tests for the sig-
niﬁcance of Sensit i v it y (z
k ) . We apply the theory developed
by Horel and Giesecke (2020) to test the null hypothesis
that the sensitivity measure is statistically different from
zero. This corresponds to a generalization of t-statistics in
linear regressions. 19 The test enables model-free inference

The partial derivatives are evaluated at the observed char-
acteristics  and  are  approximated  with  numerical  deriva-
tives.  T  is  the  number  of  periods  and  N t  is  the  num-
k )  is
ber  of  funds  available  at  time  t.  The  Sensiti v ity (z
then  averaged  over  the  three  cross-out-of-sample  folds
and  normalized  to  sum  up  to  1.  The  partial  derivative
simpliﬁes to the standard slope coeﬃcient in the special
case  of  a  linear  regression  framework.  A  larger  sensitiv-
ity means that a variable has a larger effect on the neu-

18
An alternative sensitivity measure is based on the average absolute
values of the partial derivatives. The relative importance results are very
similar to the average squared gradients, but the measure in Eq. (7) has
the advantage that we can provide a valid asymptotic inference.
19
Horel and Giesecke (2020) study the large sample asymptotic behav-
ior of gradient based variable importance measures. They view the neu-
ral network estimator as a nonparametric sieve estimator and show un-
der mild assumptions that it converges to the argmax of a Gaussian pro-
cess with mean zero and a speciﬁc covariance function. Then, they use a

109

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 5
Performance of abnormal return portfolios: Sampling Schemes.

Sampling

Information set

mean(%)

t-stat

SR

R 2
F (%)

Long-short

Random

Stock + fund+ sentiment
Fund + sentiment
Stock

0 .41
0 .40
−0 .02

4 .5 ∗ ∗ ∗
5 .4 ∗ ∗ ∗

−0 .2

0 .21
0 .25

5 .00
2 .73
−0 .01  −1 .60

Chronological

Expanding

Stock + fund+ sentiment
Fund + sentiment
Stock

Stock + fund+ sentiment
Fund + sentiment
Stock

0 .52
0 .39
0 .18

0 .45
0 .40
0 .14

5 .7 ∗ ∗ ∗
5 .2 ∗ ∗ ∗
2 .2 ∗ ∗

5 .4 ∗ ∗ ∗
5 .8 ∗ ∗ ∗
1 .7 ∗

2 .66
0 .26
0 .24
1 .49
0 .10  −1 .38

8 .92
0 .29
0 .31
5 .71
0 .09  −0 .47

This  table  reports  the  Sharpe  ratio,  mean  and  factor  R 2
of  the  top-minus-bottom
prediction-weighted decile portfolios that use different information sets for the predic-
tion. We consider three different information sets. We compare three different sampling
schemes: three random cross-out-of-sample folds, three cross-out-of-sample folds that
keep the chronological order, and estimation on an expanding window. The out-of-sample
analysis for the expanding window starts in 1990.

Fig. 12.  This ﬁgure shows the importance ranking for individual variables and variable groups. The ranking is square root of the average of the squared
gradient for the eight ensemble ﬁts. The variable importance measures are evaluated on the test data and averaged across three cross-out-of-sample folds.
Fund-speciﬁc characteristics and sentiment are used as network input.

for the importance of variables. Appendix C provides the
technical details on how we extend their model.

ter learn the non-linear interaction between sentiment and
fund-level variables, as we discuss next.

The  left  panel  of  Fig.  12  shows  the  sensitivities  for
the neural network model with fund-level information and
sentiment. Sentiment is the most important variable, fol-
lowed  by  fund  momentum,  turnover,  fund  reversal,  and
ﬂow. In the right panel, we deﬁne the variable importance
measure of a group by taking the average of the sensitiv-
ity measures within that group. The most important fund-
speciﬁc characteristics group is fund momentum character-
istics.

Table 6 reports the level and statistical signiﬁcance of
the measure for Sensit i v it y (z
k ) in the ﬁrst column of each
panel. We do not normalize the measures to add up to one.
Hence, the values represent the predicted average change
in returns. We conﬁrm that sentiment and most fund-level
characteristics  are  highly  statistically  signiﬁcant  on  a  1%
level. This is true both for our benchmark sampling scheme
in the left panel and chronological sampling in the right
panel.  One  difference  is  that  sentiment  is  quantitatively
somewhat  less  important  in  the  chronological  sampling.
The random sampling approach allows the model to bet-

functional delta method to derive the distribution of gradient based test
statistics.

110

Interaction Effects . We now analyze the interactions be-
tween sentiment and fund characteristics that are implied
by the neural network model. Fig. 13 plots the predicted
abnormal fund return (on the y -axis) as a function of one
fund-level  variable  (on  the  x -axis),  keeping  all  the  other
variables  at  their  median  level.  The  function  is  averaged
over  three  cross-out-of-sample  folds.  In  order  to  study
the interaction effects with sentiment, we plot this one-
dimensional function for different quantiles of the senti-
ment distribution. Hence, the plots show the mean of ab-
normal fund returns conditional on the values of one fund
variable and sentiment.

There  are  clear  interaction  effects  between  sentiment
and  fund-level  variables.  Predicted  abnormal  returns  are
almost  linear  in  fund-speciﬁc  variables,  but  the  slope  of
that  relationship  is  substantially  higher  in  times  of  high
sentiment. Note that without interaction effects between
sentiment  and  the  ﬂow  variable,  the  different  curves  in
each panel would be parallel shifts. They clearly are not.
The interaction effect with sentiment is particularly strong
for fund momentum in panel (a). In contrast, there is no
interaction effect for family momentum.

It  turns  out  the  interaction  effects  of  sentiment  with
fund-level variables is monotonic for all our variables. In

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 6
Statistical signiﬁcance of variable importance and interaction effects.

Random sampling

Chronological sampling

Fund characteristics

Sensitivity

Interaction

Fund characteristics

Sensitivity

Interaction

sentiment
F_r12_2
turnover
F_ST_Rev
F_r2_1
ﬂow
ages
fund_no
tna
Family_r12_2
Family_ﬂow
Family_TNA
Family_age
exp_ratio

0 .14 ∗ ∗ ∗
0 .08 ∗ ∗ ∗
0 .05 ∗ ∗ ∗
0 .04 ∗ ∗ ∗
0 .04 ∗ ∗ ∗
0 .03 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗
0 .02 ∗ ∗
0 .02 ∗
0 .01

0 .09 ∗ ∗ ∗
0 .06 ∗ ∗ ∗
0 .04 ∗ ∗ ∗
−0 .03 ∗ ∗ ∗
0 .03 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
−0 .01 ∗ ∗
0 .01 ∗ ∗
0 .01
0 .01 ∗ ∗ ∗
0 .00
−0 .01
0 .01

F_r12_2
sentiment
F_ST_Rev
F_r2_1
ﬂow
turnover
ages
Family_r12_2
tna
fund_no
exp_ratio
Family_age
Family_ﬂow
Family_TNA

0 .09 ∗ ∗ ∗
0 .08 ∗ ∗ ∗
0 .06 ∗ ∗ ∗
0 .03 ∗ ∗ ∗
0 .03 ∗ ∗ ∗
0 .03 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .02 ∗ ∗ ∗
0 .01 ∗ ∗
0 .01
0 .01

0 .06 ∗ ∗ ∗

0 .02 ∗ ∗ ∗

−0 .00

0 .02 ∗ ∗ ∗
0 .01
0 .01
0 .01
0 .01
0 .00
0 .00
0 .00
0 .01
0 .00

k )  and
This  table  reports  the  magnitude  and  signiﬁcance  of  the  measures  for  Sensit i v it y (z
Interaction (z
k , sentiment ) . Both measures are reported in percentages. Fund-speciﬁc characteristics and
sentiment are used as network input. The signiﬁcance levels are given by ∗ p < 0 . 1 ; ∗∗ p < 0 . 05 ; ∗∗∗ p <
0 . 01 . The left panel reports the results for random sampling, while the right panel shows the corre-
sponding results for chronological sampling.

order to assess the economic magnitude and the relative
importance,  we  introduce  the  following  new  interaction
measure, which measures the differences in slopes for high
and  low  macroeconomic  states.  While  we  consider  only
sentiment as macroeconomic variable in this section, we
extend this measure to other macroeconomic states in the
next section.
Interaction (z, macro )

(cid:8)
ˆ R abn ( high z, high macro ) − ˆ R abn ( low z, high macro)
(cid:8)
ˆ R abn ( high z, low macro ) − ˆ R abn ( low z, low macro )

(cid:7)
=
(cid:7)

−

.

We  evaluate  the  predicted  abnormal  return  ˆ R abn  for  the
highest  and  lowest  value  of  the  fund  variable  z and  the
high (90% quantile) and the low (10% quantile) macroeco-
nomic  state.  The  other  variables  are  set  to  their  median
values. A high absolute value in this measure indicates a
strong  interaction  effect  and  measures  the  difference  in
the return spread of characteristic z in high and low sen-
timent  states.  In  addition  to  introducing  this  new  mea-
sure, Appendix C extends the statistical distribution results
of Horel and Giesecke (2020) to test the statistical signiﬁ-
cance of interaction effects.

Table 6 reports the interaction measure for sentiment
with the fund-level characteristics. Return spreads due to
fund momentum, turnover, ﬂow and reversal are the most
affected by sentiment. The table shows that the predicted
monthly  spread  in  fund  momentum  is  nine  basis  points
higher in high sentiment states compared to low sentiment
states. The large interaction effects that we observe are sta-
tistically signiﬁcant.

Why  is  our  neural  network  structure  able  to  gen-
erate  such  an  interaction  effect  between  sentiment  and
fund-level  characteristics?  The  hidden  layer  of  the  neu-
ral  network  performs  a  nonlinear  transformation  of
original  characteristics  into  new  characteristics:  z(1) =
(0)
0  ) .  There  are  some  hidden-layer
ReLU(

(cid:5)
K
k =1 w

(0)
(0)
k  z
k

+ w

neurons that get activated only when sentiment is high ( z t
is large), which changes the dependency of the abnormal
return prediction on fund-level characteristics. When the
neuron  gets  activated,  the  slope  of  this  dependency  gets
higher, which is exactly what we see in Fig. 13 . While the
interaction effects with sentiment are the strongest, there
are also interaction effects between the fund speciﬁc vari-
ables as shown in Appendix A.1.7 .

The  interaction  effects  are  weaker  for  chronological
than  random  sampling  because  chronological  sampling
hurts  the  model’s  ability  to  learn  the  non-linear  rela-
tionship  between  fund  variables  and  sentiment,  given
that high-sentiment periods are clustered chronologically.
Appendices A.2 and A.3 discuss sensitivity and interaction
effects for chronological and expanding-window sampling.

### 4.2. Which macro-economic variable?

Having shown the importance of sentiment and its in-
teraction effects with fund characteristics, it is reasonable
to  ask  whether  other  variables  like  CFNAI  might  play  a
similarly  important  role  in  predicting  mutual  fund  out-
performance. Or maybe they add a useful piece of macro-
economic information that is not contained in sentiment?
Appendix A.1.6 answers these questions in great detail. The
main ﬁnding is that replacing sentiment with CFNAI results
does not affect much which mutual funds are sorted bot-
tom and top predicted performance deciles. However, the
relative performance prediction within the top and bottom
deciles is weaker with CFNAI than with sentiment. The rea-
son can be traced back to the much weaker interaction ef-
fects between fund variables and CFNAI.

### 4.3. A parsimonious model

In order to illustrate a more interpretable model, we es-
timate a simpliﬁed model that uses only ﬂow, F_r12_2, and
sentiment as inputs and present its functional form. Previ-
ously, we showed the results for the information set ﬂow

111

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 13.  This ﬁgure shows the predicted abnormal returns (in percentages) as a function of one fund characteristic conditional on different sentiment quan-
tiles. The other variables are set to their median. The neural network model is estimated with fund-speciﬁc characteristics and sentiment. The interaction
effects are evaluated on the test data and averaged across three cross-out-of-sample folds. The high-minus-low portfolios have a higher mean conditional
on high past sentiment. This is a non-linear interaction effect.

Table 7
Performance of abnormal return portfolios conditioned on
ﬂow + F_r12_2 + sentiment.

SR

t-stat

Decile  mean(%)

0 .40
0 .17
−0 .23

Long-short
Top
Bottom

R 2
F (%)
0 .25
0 .70
0 .16  −0 .73
0 .82
This table reports the Sharpe ratio, mean and factor R 2
of
long-short prediction-weighted, and top and bottom decile
portfolios that use only ﬂow, F_r12_2, and sentiment as in-
formation set.

5 .4 ∗ ∗ ∗
3 .4 ∗ ∗ ∗
−3 .6 ∗ ∗ ∗

−0 .21

+  fund  momentum  +  sentiment,  where  fund  momentum
refers to the fund momentum group consisting of F_r2_1,
F_r12_2, F_ST_Rev. Table 7 shows that these three variables
already capture a large fraction of the predictability. How-
ever,  the  predictability  is  weaker  than  for  a  model  that
includes  all  fund  momentum  characteristics,  which  illus-
trates the beneﬁt of F_r2_1 and F_ST_Rev.

112

This simple model with only three variables can be eas-
ily visualized and interpreted. Fig. 14 shows non-trivial in-
teraction  effects  between  the  three  variables.  The  inter-
action effects with sentiment are particularly strong. The
highest  conditional  abnormal  return  occurs  during  high
sentiment  periods  for  funds  with  high  momentum  and
high ﬂow. The lowest abnormal returns are predicted for
low sentiment periods and funds with low momentum and
low  ﬂow.  These  non-linear  interaction  effects  cannot  be
captured by a linear model. A simple ex-post regression of
abnormal returns on sentiment or high-sentiment indica-
tors is also not suﬃcient to detect these interaction effects,
since the key point is that sentiment must be included in
the prediction model itself.

Gruber  (1996)  and  Zheng  (1999)  identiﬁed  a  positive,
but fairly short-lived and weak relationship between ﬂows
and subsequent fund abnormal returns for small but not
for large funds. Importantly, Sapp and Tiwari (2004) show
that  this  “smart  money” effect  is  explained  away  once

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. 14.  This ﬁgure shows the conditional abnormal return as a function of F_r12_2, ﬂow and sentiment. The neural network only uses F_r12_2, ﬂow, and
sentiment as input. The results are shown in percentages.

the risk adjustment controls for stock return momentum.
Lou (2012) shows that the expected part of ﬂow-induced
trading  positively  forecasts  mutual  fund  returns,  while
Song (2020) ﬁnds that fund ﬂows associated with positive
factor  returns  lead  to  negative  future  fund  performance.
Our machine learning approach revives the predictive role
of ﬂows, with a 4-factor risk-adjustment, and shows that
fund ﬂow predicts performance positively and persistently.
It  also  uncovers  that  fund  abnormal  return  momentum
strongly and positively predicts fund abnormal return. Both
predictive relationships are stronger in high-sentiment pe-
riods.

These  results  are  consistent  with  theories  where  at
least  some  managers  are  skilled  and  at  least  some  in-
vestors  can  detect  skill  and  (re)allocate  their  investment
towards  skilled  managers.  There  are  reasons  to  believe
that this reallocation of investment ﬂows may not be as
strong  and  quick  as  the  frictionless  model  of  Berk  and
Green  (2004)  predicts  because  of  transaction  or  broader
search  costs  ( Roussanov  et  al.,  2021 ),  investor  inertia,  or
weak transmission from investor beliefs to allocation de-
cisions  ( Giglio  et  al.,  2021 ).  With  imperfect  reallocation,
skill leaves a trail in the form of fund return momentum
for investors to exploit in the next period. Put differently,
the ﬂows are gradual and small enough that it takes sev-
eral  periods  until  the  fund  runs  into  zero  marginal  ab-
normal returns. The results are potentially also consistent
with funds and fund families attracting ﬂows through mar-
keting rather than—or in addition to—through investment
skill ( Ibert et al., 2018; Roussanov et al., 2021 ). Marketing-
induced  inﬂows  create  buying  pressure  for  stocks  that
the fund typically invests in. In a world with downward-

sloping  demand  curves  ( Coval  and  Stafford,  2007;  Koijen
and Yogo, 2019; Gabaix and Koijen, 2021 ), this raises prices
and lifts fund returns. Through the ﬂow-performance re-
lationship,  as  well  as  through  persistence  in  marketing-
driven ﬂows, the out-performance creates more inﬂows in
the next period. The demand pressure increases prices fur-
ther, generating momentum in fund returns. The fact that
ﬂows  and  fund  momentum  have  a  much  stronger  asso-
ciation with fund performance in high-sentiment periods
lends further credence to this marketing-driven channel.

### 4.4. Decomposing abnormal returns

Having established that fund characteristics, and in par-
ticular  fund  momentum  and  ﬂow,  and  their  interaction
with sentiment are key inputs for predicting mutual fund
abnormal returns, we now try to understand in more de-
tail the mechanisms behind this prediction. For simplicity,
we do so in a univariate setting. 20 We decompose the mu-
tual funds’ abnormal return into a component that reﬂects
trading between disclosure dates (between quarter ends)
and a component that reﬂects trading within a disclosure
period (within quarter).
R abn
i,t  =

(8)

i,t − f t ˜ β
˜ R
i
(cid:9)  (cid:10)(cid:11)  (cid:12)
Between-disclosure abnormal return

i,t − f t ˜ β
i,t − f t β
i )
i − ( ˜ R
+ R
(cid:12)
(cid:10)(cid:11)
(cid:9)
Within-disclosure abnormal return

=

i,t − f t ˜ β
˜ R
i
(cid:9)  (cid:10)(cid:11)  (cid:12)
Between-disclosure abnormal return

+ R

i,t − ˜ R
i,t
(cid:9)  (cid:10)(cid:11)  (cid:12)
Return gap

+

f t ( ˜ β
i − β
i )
(cid:9)  (cid:10)(cid:11)  (cid:12)
Risk exposure difference

(9)

20

For a full set of univariate predictability results, see Appendix A.2 .

113

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 8
Decomposition of univariate long-short abnormal return factors.

Total

Between-disclosure  Within-disclosure

Risk difference

Return gap

SR

mean

SR

mean

SR

mean

SR

mean

SR

mean

F_r12_2
F_ST_Rev
Family_r12_2
Beta
Rel2High
RNA
Family_TNA
fund_no
ﬂow
Family_age
ROA
PM
ROE
ST_Rev
CF

0 .28
0 .20
0 .19
0 .15
0 .14
0 .13
0 .13
0 .13
0 .12
0 .11
0 .10
0 .10
0 .10
0 .09
0 .09

0 .36 ∗ ∗ ∗
0 .30 ∗ ∗ ∗
0 .13 ∗ ∗ ∗
0 .18 ∗ ∗ ∗
0 .20 ∗ ∗ ∗
0 .13 ∗ ∗ ∗
0 .09 ∗ ∗ ∗
0 .10 ∗ ∗ ∗
0 .11 ∗ ∗
0 .09 ∗ ∗
0 .10 ∗ ∗
0 .10 ∗ ∗
0 .11 ∗ ∗
0 .13 ∗ ∗
0 .09 ∗ ∗

0 .14
0 .14
0 .10
0 .12
0 .13
0 .11
0 .09
0 .10
0 .08
0 .08
0 .11
0 .10
0 .09
0 .06
0 .11

0 .20 ∗ ∗ ∗
0 .16 ∗ ∗ ∗
0 .09 ∗ ∗ ∗
0 .16 ∗ ∗ ∗
0 .25 ∗ ∗ ∗
0 .12 ∗ ∗ ∗
0 .07
0 .07 ∗ ∗
0 .08 ∗ ∗
0 .07
0 .13 ∗ ∗ ∗
0 .11 ∗ ∗
0 .12 ∗ ∗
0 .11
0 .16 ∗ ∗

0 .20
0 .15
0 .09
0 .03

0 .17 ∗ ∗ ∗
0 .15 ∗ ∗ ∗
0 .04 ∗ ∗
0 .03
−0 .05  −0 .05
0 .01
0 .03
0 .03
0 .03
0 .02
−0 .03  −0 .03
−0 .01  −0 .01
−0 .01  −0 .01
0 .02
−0 .07  −0 .06 ∗ ∗

0 .01
0 .05
0 .06
0 .06
0 .03

0 .02

0 .14
0 .12
0 .12

0 .11 ∗ ∗ ∗
0 .08 ∗ ∗
0 .07 ∗ ∗
−0 .01  −0 .00
−0 .03  −0 .03
−0 .03  −0 .02
−0 .12  −0 .06 ∗ ∗
−0 .12  −0 .05 ∗ ∗
−0 .00  −0 .00
−0 .13  −0 .06 ∗ ∗
−0 .05  −0 .03
−0 .03  −0 .02
−0 .02  −0 .01
0 .02
−0 .06  −0 .04

0 .02

0 .10
0 .12

0 .06 ∗ ∗ ∗
0 .06 ∗ ∗ ∗

0 .05

−0 .06  −0 .03
0 .03
−0 .03  −0 .03
0 .02
0 .08 ∗ ∗ ∗
0 .07 ∗ ∗ ∗
0 .03 ∗ ∗
0 .08 ∗ ∗ ∗
0 .01
0 .01
0 .00
0 .01
−0 .04  −0 .03

0 .04
0 .16
0 .14
0 .08
0 .13
0 .01
0 .02
0 .00
0 .01

This table reports mean and Sharpe ratio of the decomposition of univariate long-short abnormal return factors. Means of ab-
normal returns are reported in percentages. The results are sorted according to the Sharpe ratio of the long-short factors and
show the ﬁrst 15 factors. The full results are in Table A.11 . For each of the 59 characteristics and each abnormal return, we
construct decile-sorted portfolios. The long-short factors are the differences between the top decile and the bottom decile. Stars
denote the signiﬁcance levels.

The between-disclosure abnormal return is the abnor-
mal return of an investor who invests in the most recently
disclosed stock positions of a fund and holds that portfo-
lio until next fund disclosure. In the equation above,  ˜ R
i,t
is  the  hypothetical  return  of  a  mutual  fund  i  that  keeps
its portfolio weights ﬁxed at their last-disclosed levels (at
t − 1 ),  f t  is  the contemporaneous return vector  on the
Carhart  factors,  and  ˜ β
i  is  the  vector  of  exposures  to  the
Carhart factors associated with this hypothetical fund re-
i,t . 21 A positive average between-disclosure abnormal
turn  ˜ R
return means that the mutual fund can pick stocks with
positive alpha at quarterly frequency.

A  high  value  of  within-disclosure  abnormal  returns
indicates  that  the  fund  is  adding  value  by  actively
trading  between  adjacent  disclosure  dates.  The  within-
disclosure  abnormal  return  can  be  decomposed  fur-
ther  into  two  parts:  the  return  gap,  as  deﬁned  in
Kacperczyk et al. (2008) , and the risk exposure differen-
tial, which is the difference between the risk exposure of
the hypothetical ﬁxed portfolio from the latest stock hold-
ing disclosure and the real risk exposure from the current
(since rebalanced) portfolio.

We  ask  which  characteristics  best  predict  each  of
these  three  components  of  the  fund  abnormal  return.
Table 8 shows the results for the three-way decomposition.
Columns 2 and 3 report the Sharpe Ratio and mean return
associated with an investment that goes long the 10% best
funds and short the 10% worst funds based on a univariate
prediction using the variable listed in the ﬁrst column. 22

j w i, j,t R

j,t−h . That is,  ˜ R

21
The exposures  ˜ βi  are estimated from a regression of  ˜ R
Carhart factors in the previous 36 months ( h = 1 , · · · , 36 ), where ˜ R
(cid:5)

i,t−h  on the
i,t−h =
i,t−h is the return on a portfolio that holds the
identity of the stocks j and their portfolio weights w i, j,t ﬁxed at the last-
disclosed period t for every h .
22
The rows are ranked by Sharpe Ratio in the column, from highest ab-
normal return predictive SR to lowest. For brevity, we only report the ﬁrst
15 rows of this table; the full set of results appears in Table A.11 .

The next four sets of two columns predict one of the com-
ponents of the abnormal fund return.

Momentum  characteristics  in  the  ﬁrst  three  rows  of
the table are the most important characteristics for both
between-disclosure  and  within-disclosure  abnormal  re-
turns,  with  each  component  of  returns  accounting  for
about  half  of  the  return.  Flow,  the  number  of  funds  in
the  family  as  well  as  a  few  stock-speciﬁc  characteristics
are also useful for predicting between-disclosure returns,
while  these  momentum  characteristics  are  the  only  sig-
niﬁcant predictors of within-disclosure abnormal returns. 23
When it comes to understanding within-disclosure returns,
we  ﬁnd  that  fund  momentum  and  reversal  are  the  only
characteristics  that  predict  both  the  return  gap  and  the
risk difference with the same sign. Flows predict the re-
turn gap as well. Other fund and fund-family variables pre-
dict the return gap signiﬁcantly, but this effect is offset by
an opposite-sign prediction for the risk difference. That is,
while funds with these characteristics are trading in a way
that increases the fund’s return, they do so by taking on
more  systematic  risk.  Funds  with  high  fund  momentum
and  reversal  characteristics,  in  contrast,  trade  within  the
quarter in ways that both increase the return gap and re-
duce the systematic risk of the portfolio signiﬁcantly.

These univariate insights carry over to the neural net-
work prediction model as shown in Table 9 . The decompo-
sition is a complex average of the univariate results. A pre-
diction model that is only based on fund momentum, ﬂow,
and sentiment (third row of the table) has the strongest
within-disclosure  effects,  which  is  driven  in  equal  part
by the signiﬁcant positive risk difference and return gap.
Adding more fund characteristics, lowers both the within-
disclosure and between-disclosure mean returns.

An  exception  being  CF  that  is  a  signiﬁcant  negative  predictor  of

23
within and positive predictor of between.

114

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table 9
Decomposition of prediction long-short abnormal return portfolios.

Total

Between-disclosure  Within-disclosure

Risk difference

Return gap

SR

mean

SR

mean

SR

mean

SR

mean

SR

mean

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment

0 .41 ∗ ∗ ∗
0 .21
0 .40 ∗ ∗ ∗
0 .25
0 .38 ∗ ∗ ∗
0 .25
0 .28 ∗ ∗ ∗
0 .15
0 .15
0 .07
Stock  −0 .01  −0 .02

0 .10
0 .15
0 .15
0 .05
0 .04

0 .28 ∗ ∗
0 .24 ∗ ∗ ∗
0 .20 ∗ ∗ ∗
0 .13
0 .12
−0 .01  −0 .03

Flow + fund momentum+ sentiment

0 .24

0 .48 ∗ ∗ ∗

0 .14

0 .26 ∗ ∗ ∗

0 .13
0 .16
0 .17
0 .14
0 .02
0 .01

0 .17

0 .13 ∗ ∗ ∗
0 .16 ∗ ∗ ∗
0 .18 ∗ ∗ ∗
0 .15 ∗ ∗ ∗
0 .02
0 .01

0 .22 ∗ ∗ ∗

0 .07
0 .16
0 .15
0 .06
0 .00

0 .06
0 .13 ∗ ∗ ∗
0 .12 ∗ ∗ ∗
0 .06
0 .00
−0 .01  −0 .01

0 .09
0 .03
0 .08
0 .11
0 .02
0 .03

0 .06 ∗ ∗
0 .03
0 .06 ∗ ∗
0 .09 ∗ ∗ ∗
0 .02
0 .02

0 .13

0 .12 ∗ ∗ ∗

0 .11

0 .10 ∗ ∗ ∗

This table reports the mean and Sharpe ratio for the decomposition of the prediction-weighted long-short decile portfolios. We use different infor-
mation sets to predict abnormal returns. Means of abnormal returns are reported in percentages. Stars denote the signiﬁcance levels.

### 4.5. Abnormal versus total return prediction

### 4.6. Time-variation in performance

One of our key ﬁndings is that stock characteristics con-
tribute little to the prediction of best and worst funds. This
may be a surprising result, and it may appear to contra-
dict  the  ﬁndings  in  Li  and  Rossi  (2021)  who  emphasize
that one can predict the best and worst funds based on
the  stocks  that  they  hold.  We  explain  why  there  is  no
contradiction.  Our  paper  predicts  fund  abnormal  returns,
R abn
i,t  have a strong common com-
i,t  . Fund total returns R
ponent, due to fund exposures to common return factors
F t . Fig. A.15 and Table A.10 in the Appendix report the re-
sults for predicting the total returns of mutual funds rather
than abnormal returns. First, we ﬁnd that stock characteris-
tics are substantially more predictive for total fund returns
than for their abnormal returns. In other words, the stock
characteristics seem to  be able to  predict the systematic
factor component in fund returns, consistent with Li and
Rossi  (2021) . 24  However,  as  we  have  established  above,
once this factor component is taken out, stock character-
istics lose most of their predictability. Second, the Sharpe
ratio  of  long-short  portfolios  based  on  total  return  pre-
diction  is  lower  than  from  predicting  abnormal  returns.
This  points  to  an  important  methodological  contribution
of this paper. The level of fund returns (and also stock re-
turns) is extremely hard to predict, while the relative per-
formance is more predictable. Abnormal returns are a rel-
ative prediction objective as they remove the level effect
arising  from  compensation  for  systematic  risk  factor  ex-
posures.  Third,  the  comparison  between  returns  and  ab-
normal returns also illustrates the difference between con-
ditional  and  unconditional  factor  models.  Predicting  to-
tal  returns  with  a  ML  model  and  subsequently  estimat-
ing an unconditional Carhart 4-factor model on the predic-
tion portfolio returns is fundamentally different from ﬁrst
constructing abnormal returns from a conditional Carhart
4-factor model and subsequently predicting abnormal re-
turns with a ML model. Appendix A.1.9 provides a detailed
discussion.

As an aside, this result also suggests that the list of stock-speciﬁc

24
characteristics we use is not driving our results.

115

The  predictability  of  the  performance  of  mutual  fund
managers seems to be time-varying. First, the predictabil-
ity  with  stock  characteristics  only  sharply  declines  after
the year 20 0 0 as shown in Fig. 8 . In contrast, the perfor-
mance of  the strategy  that only  uses fund-speciﬁc infor-
mation continues to do reasonably well post-20 0 0. Second,
Figs. 5 and 7 show that the performance of the top deciles
based on fund-speciﬁc information and sentiment declines
post  20 0 0.  A  large  part  of  the  performance  of  the  long-
short strategy can be attributed to predicting the bottom
decile. Third, Fig. 9 indicates that performance for the top-
decile deteriorates less post-20 0 0 when funds are value-
weighted.  This  suggests  that  the  outperformance  of  the
most skilled fund managers at the largest funds is more
consistent over time, and stronger than for the most skilled
managers at the smaller funds.

This time-variation in performance is not explained by
turnover and expense ratios. Fig. A.16 shows that turnover
with consequently higher transactions costs does not sys-
tematically increase after 20 0 0. Other changes might pro-
vide an explanation. Between late 20 0 0 and early 2003 a
set of regulations were enacted that had important impli-
cations for the information collection environment, trans-
parency in securities markets, timely disclosure of informa-
tion by public ﬁrms, and reduction in trading frictions. 25
These  changes  likely  negatively  impacted  mutual  funds’
ability to generate abnormal returns both in terms of re-
ducing information collection advantages, and in facilitat-
ing  easier  and  cheaper  entry  of  arbitrageurs  competing
with mutual funds in taking advantage of potential price
anomalies. It seems possible that the largest mutual funds
have better ways of managing compliance with all these
new rules, which could at least partly help to explain the
value-weighted results.

25
The new regulations included: Reg FD requiring that when a ﬁrm dis-
closes material nonpublic information it must also make public disclosure
of that information, decimalization of quotes, Sarbanes-Oxley enacting en-
hanced transparency and accountability in ﬁnancial reporting and inter-
nal auditing mechanisms, acceleration of deadlines for ﬁling with the SEC
annual and quarterly reports to make 10-Q and 10-K ﬁlings more timely,
and NYSE’s introduction of its auto-quoting software that led to dramatic
reductions in trading frictions and costs and an equally dramatic increase
in algorithmic trading by hedge funds.

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Relatedly, Hanson and Sunderam (2014) show that the
amount  of  arbitrage  capital  devoted  to  familiar  quanti-
tative  equity  strategies,  such  as  value  and  momentum,
have  grown  dramatically  since  the  early  20 0 0s.  This  in-
ﬂux  of  capital  resulted  in  lower  strategy  returns,  whose
signals decay more rapidly following portfolio formation.
Akbas et al. (2023) document that markets are more eﬃ-
cient in responding to both ﬁrm-speciﬁc and market-wide
news  from  the  early  20 0 0s  in  comparison  to  the  period
between 1980 and 20 0 0, and that the increased eﬃciency
is related to the capacity of arbitrageurs to update prices,
as  proxied  by  the  size  and  skill  level  of  the  ﬁnance  in-
dustry. Finally, Green et al. (2017) ﬁnd a marked shift in
characteristics-based predictability in 2003 or slightly ear-
lier, which is consistent with the collapse in predictability
of stock-speciﬁc characteristics for abnormal returns.

## 5. Conclusion

In  this  paper,  we  revisit  the  question  of  predicting
actively-managed  mutual  fund  performance.  While  pre-
dictability  has  been  diﬃcult  to  establish  thus  far,  using
modern  neural  network  techniques  we  ﬁnd  strong  evi-
dence of abnormal return predictability. An important ad-
vantage  of  non-linear  neural  network  methods  is  that
they can reliably estimate a complex functional relation-
ship among a large set of variables. This turns out espe-
cially advantageous in predicting abnormal returns of mu-
tual funds. The predictability we identify is out-of-sample,
long-lived, and economically meaningful. It holds both be-
fore and after fees. Most of the beneﬁts accrue from avoid-
ing funds that the model predicts to be the worst perform-
ers. However, the prediction model is also able to identify
about 10–20% of funds that generate positive abnormal re-
turns even after fees. The predictability lasts for at least 36
months.

We  identify  two  fund  characteristics,  fund  ﬂow  and
fund  momentum,  as  key  predictors  of  mutual  fund  out-
performance. Characteristics of the stocks that funds hold
do not play a signiﬁcant role in predicting abnormal re-
turns.  Moreover,  these  two  fund  characteristics  matter
much  more  when  investor  sentiment  is  high.  A  linear
model would fail to pick up this important interaction ef-
fect. While including CFNAI, a proxy for macro-economic
activity,  also  improves  predictability,  there  are  no  dis-
cernible  interaction  effects  associated  with  CFNAI  unlike
with sentiment. These results should prove useful for im-
proving theories of delegation in the mutual fund market.
Methodologically, we show that abnormal returns, ob-
tained  as  local  residuals  to  a  factor  model,  are  not  only
an economically motivated, but also the statistically bet-
ter target for prediction. We demonstrate how to measure
dependencies on macro-economic states. We suggest that
instead of the typical horse race of model speciﬁcations it
may be better to compare the prediction and trading ben-
eﬁts by varying the information set available to the same
ﬂexible machine learning algorithm. Finally, we introduce
a novel measure for interaction effects in machine learn-
ing algorithms, which does not only measure a local slope,
but a more informative global slope. For this interpretable
measure, we provide a formal statistical signiﬁcance test.

These methodological contributions will help advance fu-
ture asset pricing and investment research using machine
learning, a growing area of research.

This paper focused on actively-managed equity mutual
funds. Natural next steps are to study bond mutual funds,
as  well  as  portfolios  managed  by  hedge  funds,  pension
funds, and endowments, in an effort to uncover both the
presence and the drivers of skill in other asset classes and
types of institutions.

## Declaration of Competing Interest

The authors have no conﬂicts of interest to declare.

## Data availability

Machine-Learning  the  Skill  of  Mutual  Fund  Managers

(Mendeley Data)

## Appendix A. Additional empirical results

### A.1. Random sampling method: Additional results

The  results  in  the  main  text  use  the  random  sample
split scheme. This appendix contains additional results ref-
erenced in the main text.

#### A.1.1. Predicted top and bottom decile returns

#### A.1.2. After-fee abnormal returns
#### A.1.3. Equally-weighted prediction portfolios

Unless explicitly mentioned, all results in the main text
are for prediction-weighted returns, where mutual funds’
abnormal  returns  in  each  prediction  decile  are  weighted
using the ML algorithm. Here we explore the alternative
of equally-weighting within each prediction decile. The re-
sults are summarized in Tables A .2 , A .3 , A .4 and Figs. A.2 ,
A .3 , A .4 , A .5 , A .6 .

#### A1.4. One-year holding period

The results in main text are based on one-month ahead
prediction. We obtain better results for longer holding pe-
riods when we estimate our model with a longer horizon
prediction objective.

In this section, we use the same network structure and
cross-out-of-sample evaluation method as in the main text,
but predict one-year ahead abnormal returns. At each time
t, we use characteristics to predict the average abnormal
return from time t + 1 to t + 12 . Fig. A.7 reports the perfor-
mance of annual abnormal return decile portfolios based
on the annual prediction target. As expected, the perfor-
mance  improves  relative  to  holding  the  one-month  pre-
diction portfolio for 12 months. We conﬁrm that the pre-
dictability lasts over longer horizons.

Fig.  A.8  plots  the  most  important  variables  for  pre-
dicting annual abnormal returns. The variable importance
changes, and shifts to more persistent fund characteristics.

116

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.1
Performance of extreme abnormal return decile portfolios.

Information set

mean(%)

Top decile

Bottom decile

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Flow + fund momentum+ sentiment
Fund exclude momentum and ﬂow
F_r12_2 + sentiment

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Flow + fund momentum+ sentiment
Fund exclude momentum and ﬂow
F_r12_2 + sentiment

0 .15
0 .17
0 .16
0 .10
0 .06
−0 .02

0 .19
−0 .01
0 .12

−0 .25
−0 .23
−0 .22
−0 .19
−0 .09
−0 .00

−0 .29
−0 .07
−0 .23

t-stat

2 .9 ∗ ∗ ∗
3 .5 ∗ ∗ ∗
3 .7 ∗ ∗ ∗
1 .7 ∗
1 .2
−0 .4

3 .2 ∗ ∗ ∗

−0 .2
2 .0 ∗ ∗

−3 .5 ∗ ∗ ∗
−3 .8 ∗ ∗ ∗
−3 .7 ∗ ∗ ∗
−2 .6 ∗ ∗ ∗
−1 .2
−0 .0

−4 .2 ∗ ∗ ∗
−1 .8 ∗
−3 .8 ∗ ∗ ∗

SR

0 .13
0 .16
0 .17
0 .08
0 .06
−0 .02

0 .15
−0 .01
0 .09

−0 .22
−0 .23
−0 .23
−0 .15
−0 .08
−0 .00

−0 .23
−0 .09
−0 .18

R 2
F (%)
1 .87
1 .46
−1 .20
−0 .52
0 .61
−2 .52

−0 .15
−0 .17
−0 .58

1 .99
1 .38
0 .74
1 .33
−0 .03
−0 .82

1 .05
−0 .32
0 .88

This table reports the Sharpe ratio, mean and factor R 2
of prediction-weighted of the ﬁrst and tenth decile portfolios that use dif-
ferent information sets for the prediction. We consider nine different information sets which combine fund-speciﬁc and stock-speciﬁc
characteristics and sentiment. We also include ﬂow and fund momentum individually.

Fig. A.1.  These ﬁgures show the cumulative abnormal after-fee returns for prediction-sorted decile portfolios. We use fund-speciﬁc characteristics and
sentiment to predict abnormal after-fee returns. The left panel weights funds based on their prediction, while the right panel equally weights funds within
the prediction deciles.

Table A.2
Performance of equally-weighted long-short abnormal return portfolios for differ-
ent information sets.

Information set  mean (%)

t-stat

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

0 .30
0 .33
0 .31
0 .21
0 .13
0 .01

4 .3 ∗ ∗ ∗
5 .9 ∗ ∗ ∗
5 .8 ∗ ∗ ∗
3 .1 ∗ ∗ ∗
1 .9 ∗
0 .1

SR

R 2
F (%)
4 .47
0 .20
3 .50
0 .27
0 .24
0 .27
2 .03
0 .14
0 .09
0 .18
0 .01  −1 .29

Flow + fund momentum+ sentiment
F_r12_2 + sentiment

0 .38
0 .38
This table reports the Sharpe ratio, mean and R 2
F  of long-short equally-weighted
decile portfolios that use different information sets to predict abnormal returns.
We consider eight different information sets which combine fund-speciﬁc and
stock-speciﬁc characteristics and sentiment. We also include ﬂow and fund mo-
mentum individually.

1 .26
0 .43

0 .26
0 .28

5 .7 ∗ ∗ ∗
6 .0 ∗ ∗ ∗

117

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.2.  The left ﬁgure shows the cumulative expense ratios of equally-weighted prediction deciles. We use the full information set (fund-speciﬁc and
stock-speciﬁc characteristics + sentiment) to predict abnormal returns before fees. The right ﬁgures shows the abnormal returns for the equally-weighted
deciles after fees, that is, the abnormal returns before fees minus the fees.

Fig. A.3.  This ﬁgure plots the cumulative abnormal returns of equally-weighted long-short decile portfolios that use different information sets to predict
abnormal returns. We consider fund-speciﬁc and stock-speciﬁc characteristics combined with sentiment.

Fig. A.4.  This ﬁgure shows the cumulative abnormal returns sorted into prediction deciles for different information sets. The returns are equally-weighted
within deciles. We consider fund-speciﬁc characteristics + sentiment, stock-speciﬁc characteristics+ sentiment, fund-speciﬁc characteristics or stock-speciﬁc
characteristics to predict abnormal returns.

118

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.5.  This ﬁgure shows the cumulative abnormal returns sorted into prediction deciles for different information sets. The returns are equally-weighted
within deciles. We consider information sets which combine fund-speciﬁc and stock-speciﬁc characteristics and sentiment to predict returns instead of
abnormal returns.

Fig. A.6.  This ﬁgure plots the cumulative return of long-short decile portfolios that use fund- or stock-speciﬁc characteristics and sentiment to predict total
returns (not abnormal returns).

119

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.3
Decomposition of equally-weighted prediction long-short abnormal return portfolios.

Total

Between-disclosure  Within-disclosure

Risk difference

Return gap

SR

mean

SR

mean

SR

mean

SR

mean

SR

mean

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

0.20
0.27
0.27
0.14
0.09
0.01

0.30 ∗ ∗ ∗
0.33 ∗ ∗ ∗
0.31 ∗ ∗ ∗
0.21 ∗ ∗ ∗
0.13 ∗ ∗
0.01

0.08
0.16
0.15
0.04
0.05
−0.01  −0.01

0.18 ∗ ∗
0.18 ∗ ∗ ∗
0.17 ∗ ∗ ∗
0.09
0.11

0.16
0.20
0.18
0.14
0.03
0.03

0.12 ∗ ∗ ∗
0.15 ∗ ∗ ∗
0.14 ∗ ∗ ∗
0.11 ∗ ∗ ∗
0.03
0.02

0.10
0.16
0.14
0.08
0.03
0.01

0.08 ∗ ∗
0.11 ∗ ∗ ∗
0.10 ∗ ∗ ∗
0.05
0.03
0.01

0.09
0.07
0.07
0.10
0.00
0.03

0.05 ∗ ∗
0.04
0.04 ∗ ∗
0.06 ∗ ∗
0.00
0.02

Flow + fund momentum+ sentiment

0.26

0.38 ∗ ∗ ∗

0.13

0.20 ∗ ∗ ∗

0.19

0.18 ∗ ∗ ∗

0.16

0.11 ∗ ∗ ∗

0.11

0.07 ∗ ∗ ∗

This table reports the mean and Sharpe ratio for the decomposition of equally-weighted long-short abnormal return portfolios. We use dif-
ferent information sets to predict abnormal returns. Means of abnormal returns are reported in percentages. The long-short portfolios are the
differences between the top decile and the bottom decile. Stars denote the signiﬁcance level.

Fig. A.7.  These panels show the out-of-sample results for prediction deciles for one-year holding periods. Each month, we predict cumulative abnormal
returns over the next 12 months with fund-speciﬁc characteristics and sentiment. Panels (a) and (b) show the overlapping cumulative annual abnormal
returns of prediction-weighted deciles and the long-short portfolio of the top decile minus the bottom decile. Panel (c) reports the Sharpe ratio, mean, and
t-statistics of the annual overlappping abnormal return long-short portfolio. The variances and standard errors are adjusted with the Newey-West estimator
with twelve lags. The performance is scaled to monthly abnormal returns.

Table A.4
Performance of equally-weighted long-short total return portfolios for
different information sets.

Information set  mean (%)

t-stat

SR

R 2
F (%)
0.14  −25.20
0.56
0.13
0.15
0.84
0.14  −18.98
0.04  −55.93

2.9 ∗ ∗ ∗
2.7 ∗ ∗ ∗
3.2 ∗ ∗ ∗
2.9 ∗ ∗ ∗
0.8

0.35
0.40
0.44
0.35
0.06

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + sentiment
Stock
This table reports the Sharpe ratio, mean and R 2
F of long-short equally-
weighted decile portfolios based on predicting returns instead of abnor-
mal returns with different information sets. We consider ﬁve different
information sets which combine fund-speciﬁc and stock-speciﬁc char-
acteristics and sentiment.

F_r12_2, which are two of the most important model pre-
dictors.

A closely related aspect is the persistence of the classi-
ﬁcation of funds. For this purpose we estimate the tran-
sition  matrix  between  prediction  quantiles  based  on  the
one-month prediction. In more detail, we count the per-
centage  of  funds  that  move  from  prediction  decile  i  to
decile  j in the next month. This transition probability is
calculated as

(cid:5)

(cid:3)

P i, j =

1
T

t

k 1 i
(cid:5)

k,t 1 j
k 1 i
k,t

k,t+1

,

#### A1.5. Persistence of signals and classiﬁcation

The prediction of returns and investment strategies for
longer horizons is directly related to the persistence of the
fund characteristics. The robustness to longer holding peri-
ods requires at least some of the characteristics to be per-
sistent. Indeed, we ﬁnd that many fund characteristics are
stable over short time horizons.

Fig. A.9 shows the autocorrelation of the fund charac-
teristics averaged over time and funds. Several fund char-
acteristics  are  very  persistent,  in  particular  turnover  and

where 1 i
at time t and decile  j at time t + 1 .

k,t is an indicator variable if a fund k is in decile i

The result is shown in Fig. A.10 . Rows correspond to i
and column to j. For example, the value of 0.22 of the (1,2)
element implies that on average 22% of the funds in the
bottom decile at time t move to the second decile at time
t + 1 . We observe that the top 20 and bottom 20 percent
of fund classiﬁcations are very persistent, which explains
why  long-short  portfolios  remain  proﬁtable  over  longer
horizons.

120

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.8.  This ﬁgure shows the importance ranking for individual variables and variable groups. The ranking is the square root of average of the squared
gradient for the eight ensemble ﬁts as in Eq. (7) . The variable importance measures are evaluated on the test data and averaged across three cross-out-
of-sample folds. Fund-speciﬁc characteristics and sentiment are used as network input. The model’s prediction target is annually averaged and overlapping
abnormal returns.

Fig. A.9.  This ﬁgure shows the persistence of fund characteristics. We estimate the autocorrelation for each time series of fund and characteristics. We
exclude time series with less than 50 observations. The ﬁgure reports the persistence as the average autocorrelation for each characteristics sorted in
increasing order.

#### A1.6. Macroeconomic conditioning variables

The main text shows the importance of sentiment and
its  interaction  effects  with  fund  characteristics.  It  is  rea-
sonable to ask whether other variables like CFNAI might
play a similarly important role in predicting mutual fund
out-performance.  Or  maybe  they  add  a  useful  piece  of
macro-economic information that is not contained in sen-
timent?  To  answer  these  questions,  we  estimate  several
additional  neural  network  models  which  combine  fund-
level information with the following macro variables: sen-
timent  (benchmark),  CFNAI,  sentiment  orthogonalized  to
CFNAI, CFNAI orthogonal to sentiment, and sentiment plus
CFNAI. 26 Table A.5 shows the results.

In  terms  of  out-of-sample  mutual  fund  return  pre-
dictability, using CFNAI leads to equally strong results in

26
We use a least-squares orthogonalization. The results are similar for
a least absolute deviation orthogonalization. Sentiment and both orthog-
onalized sentiment series are all very similar because sentiment has a
low 10% correlation with CFNAI. The prediction of abnormal fund returns
can only use a relatively small number of macroeconomic predictors as
macroeconomic variables are different from cross-sectional characteris-
tics. In our sample we have a large cross-sectional dimension, but only a
comparatively small time dimension. The effect of macroeconomic vari-
ables is estimated from the time-series, while cross-sectional variables
can take advantage from the variation in the large cross-sectional dimen-
sion. Therefore, there is simply to little time-series data to estimate a
model with a large number of macroeconomic variables.

terms of the mean and Sharpe Ratio of the long-short port-
folio. This result is surprising at ﬁrst in light of the low
correlation  between  sentiment  and  CFNAI.  However,  the
low (linear) correlation is misleading. Sorting the respec-
tive  time  series  of  sentiment,  CFNAI,  and  orthogonalized
sentiment into high, medium, and low states (terciles) re-
sults in large overlap between the states. High-sentiment
and high-CFNAI periods are often the same periods. What
matters for mutual fund abnormal return predictability is
to distinguish between the good and the bad states. This
can  be  done  equally  effectively  with  sentiment  and  CF-
NAI. Put differently, different neural network models place
very similar mutual funds into the same deciles. We calcu-
late that 78% of mutual funds that are put in the bottom
decile by  the  model that  uses  sentiment  are also  put  in
the bottom decile by the model that uses CFNAI. The corre-
sponding number for the top decile is 74%. These numbers
are even higher for the orthogonalized sentiment measure
and  when  using  both  sentiment  and  CFNAI  as  shown  in
Table A.6 .

Fig.  A.11  shows  cumulative  abnormal  returns  on
the  long-short  portfolio,  using  prediction-weighting  and
equally-weighted funds within the top and bottom deciles.
It  reinforces  the  result  that  the  four  different  macro-
economic information sets result in similarly strong out-
performance.  Consistent  with  our  previous  results,  the

121

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.10.  This matrix shows the transition probabilities of the prediction decile classiﬁcations between time t and time t + 1 . The transition probability is
deﬁned as P i, j = 1
T

k,t is an indicator variable if a fund k is in decile i at time t and decile j at time t + 1 .

, where 1 i

(cid:5)
t

(cid:5)
k,t 1 j
k 1 i
k,t+1
(cid:5)
k 1 i
k,t

Table A.5
Long-short abnormal return portfolios for different macro-economic information.

Weighting method

Information set  mean (%)

t-stat

SR

Prediction-weighted

Equally-weighted

Fund + sentiment
Fund + CFNAI
Fund + sentiment+CFNAI
Fund + sentiment_orth
Fund + CFNAI_orth
Fund

Fund + sentiment
Fund + CFNAI
Fund + sentiment+CFNAI
Fund + sentiment_orth
Fund + CFNAI_orth
Fund

0.40
0.39
0.42
0.43
0.38
0.38

0.33
0.33
0.32
0.34
0.31
0.31

5.4 ∗ ∗ ∗
6.0 ∗ ∗ ∗
6.3 ∗ ∗ ∗
6.4 ∗ ∗ ∗
5.4 ∗ ∗ ∗
5.5 ∗ ∗ ∗

5.9 ∗ ∗ ∗
6.5 ∗ ∗ ∗
6.0 ∗ ∗ ∗
6.8 ∗ ∗ ∗
5.8 ∗ ∗ ∗
5.8 ∗ ∗ ∗

0.25
0.28
0.29
0.29
0.25
0.25

0.27
0.30
0.28
0.31
0.27
0.27

R 2
F (%)
2.73
0.72
2.48
1.22
0.92
0.19

3.50
0.85
2.71
1.58
1.11
0.24

This table reports the Sharpe ratio, mean and R 2
F  of long-short prediction-weighted and
equally-weighted decile portfolios that use different macro-economic information sets for the
prediction. We consider six different macro-economic information sets: none, sentiment, CF-
NAI, sentiment orthogonal to CFNAI, CFNAI orthogonal to sentiment and sentiment+CFNAI. We
use least-squares orthogonalization.

prediction-weighting  results  in  larger  return  spreads  be-
tween the extreme deciles and hence a larger mean return.
Does  that  mean  that  the  predictions  with  sentiment
and CFNAI are equally good? No. The R 2
F  statistic is sub-
stantially higher when sentiment is used than when CFNAI
is used. In other words, the actual outperformance of the
best relative to the worst funds aligns better with the pre-
dicted outperformance when sentiment is used. The reason
is that the model with sentiment does a better job predict-
ing the actual (the cardinal and not just the ordinal) ab-
normal return of the funds in the top and bottom deciles

than the model with CFNAI. In other words, while senti-
ment and CFNAI result in similar decile rankings of funds,
the model with sentiment is substantial better in predict-
ing the level of the performance. This can be exploited for
timing the investments. Table A.7 shows the out-of-sample
performance based on sentiment terciles. The predictabil-
ity of abnormal returns is the highest for medium and high
sentiment  states.  An  investor,  who  only  invests  into  the
long-short  strategy  during  periods  of  high  predictability,
earns more than twice the expected return compared to
the low predictability state. The table also shows that even

122

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.11.  This ﬁgure plots the cumulative abnormal return returns of long-short prediction-weighted and equally-weighted decile portfolios that use
different macroeconomic information and fund-speciﬁc characteristics to predict abnormal returns. We consider the following macro-economic information
sets: none, sentiment, CFNAI, sentiment orthogonal to CFNAI and sentiment+CFNAI. We use least-squares orthogonalization.

Table A.6
Prediction based classiﬁcation relative to fund+ sentiment information.

\# bin = 2

\# bin = 5

\# bin = 10

\# bin = 20

Bin

1st

2nd

1st

5th

1st

10th

1st

20th

Fund + CFNAI
Fund + sentiment_orth
Fund + CFNAI_orth
Fund + sentiment and CFNAI
Fund
Stock + sentiment
Stock

0.91
0.95
0.91
0.94
0.93
0.55
0.55

0.91
0.95
0.91
0.94
0.93
0.55
0.55

0.84
0.89
0.83
0.87
0.87
0.27
0.27

0.82
0.89
0.83
0.89
0.86
0.27
0.27

0.78
0.85
0.78
0.83
0.81
0.17
0.17

0.74
0.81
0.74
0.82
0.78
0.15
0.16

0.70
0.79
0.70
0.75
0.73
0.11
0.11

0.61
0.70
0.61
0.73
0.67
0.08
0.08

This ﬁgure shows the percentage of funds that overlap with the prediction quantiles based on fund+
sentiment information. We consider two, ﬁve, 10 or 20 quantiles and six different information sets
for predicting abnormal returns. The reference classiﬁcation is fund + sentiment.

Table A.7
Long-short abnormal return portfolios in different sentiment terciles.
T L

T M

T H

Portfolio

SR

mean

t-stat

R 2
F

SR

mean

t-stat

R 2
F

SR

mean

t-stat

R 2
F

0 .12
−0 .11
−0 .19
−0 .12
−0 .15
−0 .09
−0 .09
−0 .15
−0 .10
−0 .06
0 .05

0 .23
−0 .18
−0 .16
−0 .09
−0 .10
−0 .06
−0 .06
−0 .09
−0 .06
−0 .05
0 .04

D10-D1
D1
D2
D3
D4
D5
D6
D7
D8
D9
D10

0 .50
0 .37
0 .71  −0 .25
1 .77  −0 .15
0 .80  −0 .05
0 .01
1 .10
0 .01
0 .44
0 .12
0 .67
0 .10
1 .05
0 .15
−0 .55
0 .19
−0 .80
0 .22
−0 .86
This table reports the Sharpe ratio, mean, t-statistic of mean and R 2
mean and R 2
of the three folds, and represent a valid out-of-sample performance. We use fund-speciﬁc characteristics and sentiment to predict abnormal returns.

3 .39
0 .32
3 .65  −0 .23
1 .77  −0 .05
0 .03
1 .14
−0 .53  −0 .07
0 .01
0 .06
0 .15
0 .14
0 .07
0 .21

F are reported in percentages. The low, medium and high tercile ( T L

F of prediction-weighted decile portfolios evaluated in different sentiment terciles. The
) splits for sentiment are based on the in-sample data of each

4 .83
1 .35
−3 .43
−7 .41
−4 .49
−2 .90
−3 .20
−0 .43
−1 .69
−0 .12
2 .68

0 .42
−0 .23
−0 .10
−0 .04
0 .01
0 .01
0 .07
0 .06
0 .10
0 .24
0 .19

0 .55
−0 .29
−0 .04
0 .02
−0 .06
0 .00
0 .04
0 .11
0 .12
0 .08
0 .27

4 .6 ∗ ∗ ∗
−3 .1 ∗ ∗ ∗
−1 .8 ∗
−0 .7
0 .1
0 .2
1 .5
1 .2
1 .8 ∗
2 .3 ∗ ∗
2 .7 ∗ ∗ ∗

4 .0 ∗ ∗ ∗
−2 .9 ∗ ∗ ∗
−0 .6
0 .4
−0 .9
0 .1
0 .7
1 .9 ∗
1 .7 ∗
0 .9
2 .6 ∗ ∗

1 .6
−1 .4
−2 .4 ∗ ∗
−1 .5
−1 .9 ∗
−1 .1
−1 .2
−1 .8 ∗
−1 .2
−0 .8
0 .6

0 .49
−0 .85
−0 .12
−1 .01
−0 .32
1 .00

and T H

, T M

investors who can only take long positions can still achieve
an average monthly  abnormal return  of 0.27% by invest-
ing into the top funds in high sentiment periods. Note that
these results represent a valid out-of-sample performance
as  the  strategy  uses  lagged  sentiment  and  estimates  the
terciles cut-offs without the use of out-of-sample data.

#### A1.7. Interaction effects

To  help  understand  the  origin  of  the  weaker  perfor-
mance of the model with CFNAI, Fig. A.12 revisits the in-
teraction effects of fund-level characteristics with CFNAI. It
shows no interaction effects: the predictive effect of a fund
characteristic on abnormal returns in high CFNAI periods is

123

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.8
Interaction for fund-speciﬁc characteristics in the neural network model.

ﬂow

F_r12_2

F_ST_Rev

Family_r12_2

turnover

F_r12_2
F_ST_Rev
Family_r12_2
turnover
F_r2_1

0.251
0.068
0.037
0.004
0.080

0.336
0.147
0.070
0.284

0.018
0.050
0.049

−0 .020

0 .048  −0.007

This table shows the interaction measure between the fund-speciﬁc characteristics.
The results are presented in basis points. The neural networks use fund-speciﬁc char-
acteristics and sentiment as input.

Fig. A.12.  This ﬁgure shows the predicted abnormal returns (in percentages) as a function of one fund characteristic and different CFNAI quantiles. The
other variables are set to their median values. The neural network model is estimated with fund-speciﬁc characteristics and CFNAI. The interaction effects
are evaluated on test data and averaged across three cross-out-of-sample folds. The high-minus-low factors have almost the same mean conditional on
different past CFNAI. There is essentially no interaction effect.

a parallel shift from the relationship in low-CFNAI periods.
This is in contrast to the strong interaction effects for sen-
timent.

Fig.  A.13  compares  the  interaction  measure  for  senti-
ment (orange bars) and CFNAI (black bars) with the fund
characteristics. As noted in the main text, return spreads
due  to  fund  momentum,  turnover,  ﬂow  and  reversal  are
the most affected by sentiment. In contrast, CFNAI has vir-
tually no interaction with the fund characteristics.

We assess more general interactions between different
fund characteristics. Here, we calculate the interactions be-
tween  fund-speciﬁc  characteristics.  The  interaction  mea-

124

sure is deﬁned similar to the main text as:

Interaction (z i , z j )
(cid:8)
(cid:7)
ˆ R abn ( high z i , high z j ) − ˆ R abn ( low z i , high z j )
=
(cid:7)

(cid:8)
ˆ R abn ( high z i , low z j ) − ˆ R abn ( low z i , low z j )

−

.

i  and  z

We  set  the  high  values  of  z
j  to  0.5,  and  the
low  value  to  −0.5,  which  makes  the  measure  symmet-
j ) =
ric  with respect to  z
Interaction (z
i ) . The other variables are set to their me-
dian values. The results are presented in Table A.8 .

j ,  that  is,  Interaction (z

i  and z

j , z

i , z

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.13.  This ﬁgure reports the measure Interaction(z,macro) for fund characteristics and sentiment and CFNAI as macro-economic variables. We evaluate
the predicted abnormal return ˆ R abn
for the highest and lowest value of the fund variable z and the high (90% quantile) and the low (10% quantile) macro-
economic state. The other variables are set to their median values. The measure is reported in percentages.

Fig. A.14.  These ﬁgures show the cumulative abnormal returns of the long-short portfolios with prediction-weights for mutual funds with at least 15
million asset under management and for prediction-value-weights. We predict abnormal returns with fund-speciﬁc characteristics and sentiment. The left
subﬁgure shows the results for mutual funds with at least 15 million asset under management, while the right subﬁgure uses prediction-value weighted
portfolios.

#### A1.8. Robustness to size of funds

The  predictability  is  robust  to  excluding  or  down-
weighting small mutual funds. We ﬁrst present the results
after excluding small mutual funds and second for value-
weighted prediction portfolios.

We  exclude  mutual  funds  with  less  than  15  million
asset  under  management  (TNA),  which  is  an  often  used
cutoff in  the  literature.  Figs.  9  and  A.14  and  Table  A.9
show  the  results  for  prediction  weighted  portfolios.  The
predictability  is  essentially  not  affected  by  dropping  the
smaller  funds  and  our  results  are  not  driven  by  small
funds.

As shown in the main text, prediction-weighted portfo-
lios use normalized model predictions as portfolio weights
and thus take advantage of both the ranking and relative
magnitude information. The prediction based weights are
deﬁned in Eq. (6) , where  ˜ μ
i,t  are the normalized predic-
tion weights. Value-weighted portfolios assign proportion-
ally larger weights to funds with more assets under man-

agement (aum). We combine the prediction with the value
of funds to form predication-value weights
˜ μi,t × aum i,t
(cid:5)
N
i =1 ˜ μi,t × aum i,t

w pred,val
i,t

=

Figs. 9 and A.14 and Table A.9 summarize the results
for prediction-value weighted portfolios and show that the
predictability is overall robust to value weighting.

#### A1.9. Abnormal versus total return prediction

Li and Rossi (2021) predict total mutual fund returns,
i,t , while our paper predicts fund abnormal returns, R abn
R
i,t  .
Fund total returns have a strong common component, due
to fund exposures to common return factors F t . Fig. A.15
and Table A.10 report the results for predicting the total re-
turns of mutual funds rather than abnormal returns. First,
stock characteristics are substantially more predictive for
total fund returns than for their abnormal returns. In other
words, the stock characteristics seem to be able to predict

125

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.15.  This ﬁgure plots the cumulative returns sorted into prediction deciles for different information sets. The returns are prediction-weighted within
deciles. We consider information sets which combine fund-speciﬁc and stock-speciﬁc characteristics and sentiment to predict returns instead of abnormal
returns.

Table A.9
Results for abnormal return prediction portfolios for mutual funds larger
than 15 million and for value weights.

Decile

mean(%)

t-stat

SR

R 2
F (%)

Prediction-weighted with size cutoff

Long-short
Top
Bottom

Long-short
Top
Bottom

0 .40
0 .17
−0 .23

6 .5 ∗ ∗ ∗
3 .9 ∗ ∗ ∗
−4 .5 ∗ ∗ ∗

0 .30
0 .18
−0 .23

Prediction-value-weighted

0 .35
0 .18
−0 .18

4 .3 ∗ ∗ ∗
3 .0 ∗ ∗ ∗
−2 .8 ∗ ∗ ∗

0 .20
0 .14
−0 .14

4 .07
2 .03
2 .05

2 .30
1 .12
0 .76

This table shows the out-of-sample results for prediction-sorted portfo-
lios for mutual funds with at least 15 million asset under management
and for prediction-value-weights using all funds. We predict abnormal
returns with fund-speciﬁc characteristics and sentiment. We report the
out-of-sample Sharpe ratios, mean returns and t-statistics of the long-
short portfolio.The top subtable shows the results for mutual funds with
at least 15 million asset under management, while the bottom table uses
prediction-value weighted portfolios with all funds.

Table A.10
Performance of long-short return portfolios for different information sets.

Data  mean(%)

t-stat

SR

R 2
F (%)
-26 .54
0 .97
0 .97
-20 .03
-53 .21

3 .1 ∗ ∗ ∗
3 .0 ∗ ∗ ∗
3 .5 ∗ ∗ ∗
3 .1 ∗ ∗ ∗
1 .1

0 .45
0 .49
0 .53
0 .44
0 .11

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + sentiment
Stock

0 .14
0 .14
0 .16
0 .14
0 .05
This table reports the Sharpe ratio, mean and factor R 2
of long-short
prediction-weighted decile portfolios based on predicting total returns in-
stead of abnormal returns with different information sets. We consider
ﬁve different information sets which combine fund-speciﬁc and stock-
speciﬁc characteristics and sentiment to predict returns instead of abnor-
mal returns.

the systematic factor component in fund returns, consis-
tent  with  Li  and  Rossi  (2021) .  However,  as  we  have  es-
tablished above, once this factor component is taken out,
stock  characteristics  lose  most  of  their  predictability.  In-
deed, our object of interest, abnormal returns, is orthog-

126

onal to the systematic component of fund returns by con-
struction. It is this systematic component of returns that is
predicted by stock characteristics. Second, the Sharpe ra-
tio  of  long-short  portfolios  based  on  total  return  predic-
tion is lower than from predicting abnormal returns. The
Sharpe ratio in Table A.10 are only about 0.15. This points
to an important methodological contribution of this paper.
The  level  of  fund  returns  (and  also  stock  returns)  is  ex-
tremely hard to predict, while the relative performance is
more predictable. Abnormal returns remove the level ef-
fect arising from compensation for systematic  risk factor
exposures. Hence, an abnormal return prediction objective
is mainly a relative objective. In contrast, a machine learn-
ing prediction for returns might not select a model with
a correct relative cross-sectional ranking of funds if it has
a high prediction error in the level, which is largely irrel-
evant for relative ranking. In summary, abnormal returns
are not only the object of interest to us, since we want to
measure the returns managers earn in excess of systematic
risk compensation, but they may also be the better objec-
tive for machine learning prediction in a statistical sense.

The comparison between returns and abnormal returns
also illustrates the difference between conditional and un-
conditional  factor  models.  The  abnormal  returns  are  es-
timated  from  a  factor  model  using  rolling-window  re-
gressions  and  hence  reﬂect  time-varying  risk  exposure.
Holding-based  stock  characteristics  seem  to  predict  the
time-varying risk exposure of the factors. The residuals of
these local regressions take out the component that is pre-
dictable with holding-based stock characteristics.

As  a  coda  to  this  discussion,  predicting  total  returns
with a ML model and subsequently estimating an uncon-
ditional Carhart 4-factor model on the prediction portfo-
lio returns is fundamentally different from ﬁrst construct-
ing abnormal returns from a conditional Carhart 4-factor
model and subsequently predicting abnormal returns with
a ML model. It is possible to ﬁnd signiﬁcant unconditional
alphas for mutual fund portfolio returns formed from to-
tal  return  predictions  using  only  stock  characteristics,  as
shown in Table A.13 . However, once we obtain local resid-

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.16.  These ﬁgures show the 12-months moving average of expense and turnover ratios for the equally- and prediction-weighted deciles. The infor-
mation set for the prediction are all characteristics and sentiment. We use the benchmark random sampling.

uals with respect to Carhart factors, the stock characteris-
tics lose most of their predictability. As we showed, these
residuals depend almost entirely on fund-speciﬁc charac-
teristics and sentiment.

#### A1.10. Turnover and expense ratios over time

Fig.  A.16  plots  turnover  and  expense  ratios  among
predicted  performance  deciles.  There  are  no  systematic
changes  over  time  that  differ  between  the  top-  and
bottom-predicted performance portfolios in either the ex-
pense ratio or the turnover ratio.

### A2. Chronological sampling method

The results in the main text apply a random cross-out-
of-sample analysis, where the time periods for the three

folds are sampled randomly to ensure that low and high
sentiment states are represented in all three folds. The pre-
dictability results are robust to a cross-out-of-sample anal-
ysis with chronological sampling. This shows that the pre-
dictability in the main text is not driven by our sample se-
lection.

The  chronological  cross-out-of-sample  analysis  keeps
the  chronological  order  of  observations  within  the  folds.
Exactly as in the main text, we use two of the folds to es-
timate the model and select the tuning parameters (two-
thirds of the sample), and evaluate the prediction out-of-
sample  on  the  remaining  fold  (one-third  of  the  sample).
We repeat the estimation for three different combinations
to obtain an out-of-sample prediction for each observation
in the sample.

127

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.17.  These ﬁgures show the cumulative abnormal returns sorted into prediction deciles for different information sets. The abnormal returns are
prediction-weighted within deciles. We consider fund-speciﬁc characteristics + sentiment, stock-speciﬁc characteristics+ sentiment, stock-speciﬁc character-
istics or all characteristics to predict abnormal returns. Three cross-out-of-sample folds keep the chronological order.

#### A2.1. Long-short portfolio results

This subsection conﬁrms that our main ﬁndings on ab-
normal returns are robust to chronological sampling. We
can still strongly predict out-of-sample the abnormal re-
turns of mutual fund managers, and the mean spread in
skill between the top and bottom fund managers is simi-
lar to random sampling. Fund characteristics still have the
strongest predictive power, but now the predictability with
stock characteristics is stronger than before. However, the
economic and statistical signiﬁcance of stock characteris-
tics is still much weaker compared to fund characteristics.
When we zoom in on the time series of long-short port-
folios, stock characteristics lose their predictive power af-
ter the year 20 0 0. Fund momentum, ﬂow, and sentiment
still emerge as the most important variables for predicting
abnormal  returns.  Consistent  with  our  intuition,  the  role
of investor sentiment is now weaker: it shows up as the
second most important variable in the variable importance
ranking and the interaction effects between fund variables
and sentiment is weaker.

The cumulative abnormal returns for different informa-
tion sets are in Fig. A.17 , the cumulative abnormal returns

of  long-short  prediction  portfolios  are  in  Fig.  A.18 .  The
Sharpe ratio, mean, and factor R 2  of long-short, the ﬁrst,
and the tenth prediction-weighted decile portfolios are in
Table A.11 .

#### A2.2. Holding period

This  subsection  shows  that  the  persistence  of  perfor-
mance in our long-short portfolio is robust to chronolog-
ical sampling. Fig. A.19 shows the abnormal returns on a
long-short prediction portfolio for holding periods ranging
from 1 month to 36 months under chronological sampling.

#### A2.3. Interaction effects

This subsection studies the interaction effects between
fund  characteristics  and  sentiment  under  chronological
sampling.  The  interaction  effects  between  sentiment  and
fund variables are less pronounced than with random sam-
pling,  but  the  interaction  effects  between  sentiment  and
fund momentum, fund short term reversal, and ﬂow are
still signiﬁcant, as in the main text.

The  top  variable  importance  for  explaining  abnormal
returns  and  interaction  effects  between  sentiment  and

128

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.11
Performance of abnormal return portfolios with chronological data split.

Portfolio

Long-short

Top Decile

Bottom Decile

Information set

mean(%)

t-stat

SR

R 2
F (%)

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Fund + CFNAI
Flow + fund momentum+ sentiment
Fund exclude momentum and ﬂow
F_r12_2 + sentiment

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Fund + CFNAI
Flow + fund momentum+ sentiment
Fund exclude momentum and ﬂow
F_r12_2 + sentiment

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

Fund + CFNAI
Flow + fund momentum+ sentiment
Fund exclude momentum and ﬂow
F_r12_2 + sentiment

0 .52
0 .39
0 .41
0 .40
0 .20
0 .18

0 .36
0 .47
0 .00
0 .32

0 .20
0 .17
0 .18
0 .16
0 .14
0 .10

0 .14
0 .19
−0 .03
0 .10

−0 .32
−0 .22
−0 .23
−0 .23
−0 .07
−0 .08

−0 .22
−0 .27
−0 .03
−0 .22

5 .7 ∗ ∗ ∗
5 .2 ∗ ∗ ∗
5 .6 ∗ ∗ ∗
4 .9 ∗ ∗ ∗
2 .9 ∗ ∗ ∗
2 .2 ∗ ∗

5 .2 ∗ ∗ ∗
5 .3 ∗ ∗ ∗
0 .1
4 .0 ∗ ∗ ∗

4 .5 ∗ ∗ ∗
3 .6 ∗ ∗ ∗
3 .9 ∗ ∗ ∗
3 .3 ∗ ∗ ∗
2 .7 ∗ ∗ ∗
2 .4 ∗ ∗

3 .1 ∗ ∗ ∗
3 .6 ∗ ∗ ∗

−0 .8
1 .6

−4 .1 ∗ ∗ ∗
−3 .6 ∗ ∗ ∗
−3 .8 ∗ ∗ ∗
−3 .5 ∗ ∗ ∗
−1 .2
−1 .1

−3 .9 ∗ ∗ ∗
−4 .0 ∗ ∗ ∗
−1 .0
−3 .6 ∗ ∗ ∗

0 .26
0 .24
0 .26
0 .23
0 .13
0 .10

0 .24
0 .24
0 .00
0 .19

0 .21
0 .17
0 .18
0 .15
0 .12
0 .11

0 .14
0 .17
−0 .03
0 .08

−0 .33
−0 .22
−0 .23
−0 .22
−0 .06
−0 .08

−0 .22
−0 .23
−0 .04
−0 .16

2 .66
1 .49
0 .52
−0 .78
-13 .48
−1 .38

1 .15
1 .12
0 .10
0 .88

−3 .65
−0 .44
−1 .63
−7 .07
−7 .98
−6 .38

−1 .72
−0 .05
−0 .52
−0 .05

2 .93
1 .03
0 .30
1 .95
−5 .46
0 .31

0 .64
0 .76
−0 .04
0 .56

This table reports the Sharpe ratio, mean and factor R 2
of long-short, the ﬁrst, and the tenth prediction-weighted decile portfolios that use
different information sets for the prediction. We consider nine different information sets which combine fund-speciﬁc and stock-speciﬁc char-
acteristics and sentiment. We also include ﬂow and fund momentum (F_r12_2, F_r2_1 and F_ST_Rev) individually. The cross-out-of-sample folds
keep the chronological order in each fold.

Fig. A.18.  This ﬁgure plots the cumulative abnormal returns of prediction-weighted long-short decile portfolios that use different information sets for
prediction. We consider fund-speciﬁc and stock-speciﬁc characteristics combined with sentiment. Three cross-out-of-sample folds keep the chronological
order.

129

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.19.  This ﬁgure shows the results for long-short prediction-weighted portfolios for different holding periods. The time periods are sampled chrono-
logically. At each time t, we sort funds based on the one-month prediction into deciles and hold the long-short prediction portfolio for s months with
overlapping returns. We calculate the mean, Sharpe ratio, standard deviation, and t-statistics of the overlapping abnormal returns. The one-month predic-
tion uses either fund+sentiment, stock+fund+sentiment or ﬂow+fund+sentiment.

fund characteristics are in Figs. A.20 and A.21 . Since the
third  chronological  fold  does  not  include  any  high  sen-
timent  states,  there  is  mechanically  no  interaction  ef-
fect  with  sentiment  for  this  speciﬁc  fold.  As  a  result,
Fig. A.20 shows that the importance of sentiment declines.
A model evaluation that would only use the last fold to as-
sess the conditional abnormal return would not detect the
strong interaction effects with sentiment.

Fig. A.21 plots the mean of abnormal fund returns con-
ditional on the values of one fund variable and sentiment.
It  shows  that  the  interaction  effects  between  sentiment
and fund variables are less pronounced compared to the
interaction effects at random sampling.

Fig. A.22 plots the mean of abnormal fund returns con-
ditional  on  CFNAI.  It  shows  weak  interaction  effects  be-
tween CFNAI and fund characteristics, just like in the ran-
dom sampling approach.

#### A2.4. Predicting total returns

Table A.12 shows the results for predicting total (as op-
posed to abnormal) return with various information sets
under chronological sampling. Table A.13 shows exp-post
unconditional factor regressions on total return prediction
long-short portfolios. The alphas are signiﬁcant and the R 2
modest.

### A3. Expanding-window sampling method

This section studies how our results change under an
expanding window estimation of the neural network. This
model  assumes  a  time-varying  conditional  abnormal  re-
turn function, in contrast with the constant abnormal re-
turn  function  assumed  in  the  random  and  chronologi-
cal  cross-validation  exercises.  We  predict  abnormal  re-
turns with an expanding window estimation, updating the

130

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.20.  This ﬁgure shows the importance ranking for individual variables and variable groups. The ranking is the square root of average of the squared
gradient for the eight ensemble ﬁts as in Eq. (7) . The variable importance measures are evaluated on the test data and averaged across three cross-out-of-
sample folds. Fund-speciﬁc characteristics and sentiment are used as network input. Three cross-out-of-sample folds keep the chronological order.

Fig. A.21.  This ﬁgure shows the predicted abnormal returns (in percentages) as a function of one fund characteristic conditional on different sentiment
quantiles. The other variables are set to their median. The neural network model is estimated with fund-speciﬁc characteristics and sentiment. The interac-
tion effects are evaluated on the test data and averaged across three cross-out-of-sample folds. The cross-out-of-sample folds keep the chronological order
in each fold. The high-minus-low portfolios have a higher mean conditional on high past sentiment. This is a non-linear interaction effect.

model  every  year.  Since  we  need  to  “warm  start” the
model, the analysis now starts in the year 1990.

The cumulative abnormal returns for different informa-
tion  sets  are  in  Fig.  A.23 .  The  cumulative  abnormal  re-
turns  of  long-short  prediction  portfolios  are  in  Fig.  A.24 .

The  Sharpe  ratio,  mean,  and  factor  R 2  of  the  long-short,
the  ﬁrst,  and  the  tenth  prediction-weighted  decile  port-
folios are in Table A.14 . These results establish the strong
predictability of fund manager skill and the important role
of fund characteristics for prediction. The predictive power

131

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.22.  This ﬁgure shows the predicted abnormal returns (in percentages) as a function of one fund characteristic conditional on different CFNAI quan-
tiles. The other variables are set to their median. The neural network model is estimated with fund-speciﬁc characteristics and CFNAI. The interaction
effects are evaluated on the test data and averaged across three cross-out-of-sample folds. The cross-out-of-sample folds keep the chronological order in
each fold.

132

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.23.  These ﬁgures show the cumulative abnormal returns sorted into prediction deciles for different information sets. The returns are prediction-
weighted within deciles. We consider fund-speciﬁc characteristics + sentiment, stock-speciﬁc characteristics+ sentiment, stock-speciﬁc characteristics or all
characteristics to predict abnormal returns. The model predictions are generated in a rolling way. That is, we use data until year to generate predictions
for year t + 1 , with t varying. To make sure that we have enough training data for out-of-sample evaluations, we start the out-of-sample analysis on year
1990.

Fig. A.24.  This ﬁgure plots the cumulative abnormal returns of prediction-weighted long-short decile portfolios that use different information sets for
prediction. We consider fund-speciﬁc and stock-speciﬁc characteristics combined with sentiment. The model predictions are generated in a rolling way.
That is, we use data until year to generate predictions for year t + 1 , with t varying. To make sure that we have enough training data for out-of-sample
evaluations, we start the out-of-sample analysis on year 1990.

133

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.12
Performance of long-short total return portfolios for different information sets
with chronological data split.

Information set

mean(%)

t-stat

SR

Stock + fund+ sentiment
Fund + sentiment
Fund
Stock + fund
Stock + sentiment
Stock

0.63
0.65
0.61
0.47
0.62
0.42

4.8 ∗ ∗ ∗
3.6 ∗ ∗ ∗
3.6 ∗ ∗ ∗
4.1 ∗ ∗ ∗
5.0 ∗ ∗ ∗
3.8 ∗ ∗ ∗

0.22
0.17
0.16
0.19
0.23
0.17

R 2
F (%)

−1 .68
0 .56
0 .22
−5 .48
0 .62
−3 .19

This table reports the Sharpe ratio, mean and factor R 2
of long-short prediction-
weighted decile portfolios based on total return prediction with different infor-
mation sets. We consider six different information sets which combine fund-
speciﬁc and stock-speciﬁc characteristics and sentiment. Three cross-out-of-
sample folds keep the chronological order and the network structure is the
same as the benchmark setup for predicting abnormal returns other than l1
penalty = 1 e − 5 .

Table A.13
Spanning of long-short return prediction portfolios with different factor models and chronological data split.

Stock + fund+ sentiment

Fund + sentiment

Fund

Stock + fund

Stock + sentiment

Stock

FF 4 factors
R 2

α

FF 5 factors
R 2

α

FF 6 factors
R 2

α

FF 8 factors
R 2

α

0.19 ∗ ∗ ∗
(0.04)
0.14 ∗ ∗ ∗
(0.03)
0.15 ∗ ∗ ∗
(0.03)
0.16 ∗ ∗ ∗
(0.04)
0.20 ∗ ∗ ∗
(0.04)
0.14 ∗ ∗ ∗
(0.04)

0.08

0.15

0.09

0.16

0.11

0.24

0.19 ∗ ∗ ∗
(0.04)
0.18 ∗ ∗ ∗
(0.03)
0.17 ∗ ∗ ∗
(0.03)
0.23 ∗ ∗ ∗
(0.04)
0.20 ∗ ∗ ∗
(0.04)
0.24 ∗ ∗ ∗
(0.04)

0.05

0.07

0.04

0.05

0.07

0.09

0.16 ∗ ∗ ∗
(0.04)
0.14 ∗ ∗ ∗
(0.03)
0.14 ∗ ∗ ∗
(0.03)
0.19 ∗ ∗ ∗
(0.04)
0.17 ∗ ∗ ∗
(0.04)
0.19 ∗ ∗ ∗
(0.04)

0.09

0.16

0.09

0.18

0.12

0.27

0.20 ∗ ∗ ∗
(0.04)
0.20 ∗ ∗ ∗
(0.03)
0.22 ∗ ∗ ∗
(0.03)
0.23 ∗ ∗ ∗
(0.04)
0.21 ∗ ∗ ∗
(0.04)
0.22 ∗ ∗ ∗
(0.04)

0.25

0.51

0.58

0.36

0.23

0.36

mean μ

0.22 ∗ ∗ ∗
(0.05)
0.17 ∗ ∗ ∗
(0.05)
0.16 ∗ ∗ ∗
(0.05)
0.19 ∗ ∗ ∗
(0.05)
0.23 ∗ ∗ ∗
(0.05)
0.17 ∗ ∗ ∗
(0.05)

This table reports the time-series regression results of long-short prediction-weighted decile portfolios for different
factor models. The model predictions are based on machine learning predictions on fund returns with different in-
formation sets. Three cross-out-of-sample folds keep the chronological order and the network structure is the same
as the benchmark setup for predicting abnormal returns other than l1 penalty = 1 e − 5 . We consider the 4-factor
Fama-French-Carhart model (market, size, value and momentum), the 5-factor Fama-French model (market, size, value,
proﬁtability and investment), a 6-factor model which adds the momentum factor to the Fama-French 5 factors, and
an 8-factor model which adds the momentum, short-term reversal and long-term reversal factors to the Fama-French
5 factors. The α column reports the time-series pricing error and R 2
is the explained variation of the regression. Both
the long-short abnormal return portfolios and the factor models are normalized to have a standard deviation of 1.
Standard errors are in brackets and stars denote the signiﬁcance levels.

of stock characteristics also remains weaker compared to
information sets that include fund information.

Figs. A.25 and A.26 show that the important predictive
role of fund momentum and fund ﬂow and the interaction
effects between fund variables and sentiment remain ro-
bust.

## Appendix B. Implementation: Tuning parameters

Table  B.1  summarizes  the  tuning  parameters  for  the
possible  network  structures.  HU,  the  number  of  hidden
units in each layer, deserves more explanation. The nodes
of ﬁrst layer are 64 or 32 and the number of nodes in each
layer is half of the previous layer. For example, for a neu-
ral network with 3 layers the number of nodes are 32 , 16 , 8
and 64 , 32 , 16 . In mathematical terms the number of nodes
in the i th layer is 2 7 −i or 2 6 −i .

We  obtain  robust  and  stable  ﬁts  by  ensemble  aver-
aging  over  several  ﬁts  of  the  models.  A  distinguishing
feature  of  neural  networks  is  that  the  estimation  results
can  depend  on  the  starting  value  used  in  the  optimiza-
tion. The standard practice which has also been used by
Chen et al. (2023) is to train the models separately with
different initial values chosen from an optimal distribution.
Averaging over multiple ﬁts achieves two goals: First, it di-
minishes the effect of a local suboptimal ﬁt. Second, it re-
duces the estimation variance of the estimated model. All
our neural networks are averaged over eight model ﬁts.

We split the full time-series sample into three periods
of the same length but select the dates randomly for each
fold as shown in Fig. 2 . We keep the same three randomly
selected folds throughout our analysis. We use two of the
periods to estimate the model and select the tuning pa-

134

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Table A.14
Performance of abnormal return portfolios with rolling-window predictions.

Portfolio

Long-short

Top decile

Bottom decile

Information set  mean(%)

t-stat

SR

R 2
F (%)

Stock + fund+ sentiment
Fund + sentiment
Stock + sentiment
Stock

Stock + fund+ sentiment
Fund + sentiment
Stock + sentiment
Stock

Stock + fund+ sentiment
Fund + sentiment
Stock + sentiment
Stock

0 .45
0 .40
0 .24
0 .14

0 .20
0 .18
0 .11
0 .03

−0 .25
−0 .22
−0 .13
−0 .11

5 .4 ∗ ∗ ∗
5 .8 ∗ ∗ ∗
2 .8 ∗ ∗ ∗
1 .7 ∗

3 .2 ∗ ∗ ∗
3 .4 ∗ ∗ ∗
1 .9 ∗
0 .5

0 .29
0 .31
0 .15
0 .09

0 .17
0 .18
0 .10
0 .03

−4 .0 ∗ ∗ ∗
−4 .1 ∗ ∗ ∗
−2 .1 ∗ ∗
−1 .6

−0 .21
−0 .23
−0 .12
−0 .10

8 .92
5 .71
2 .78
−0 .47

0 .13
−1 .37
−1 .29
−2 .75

3 .31
−1 .44
0 .42
0 .57

This table reports the Sharpe ratio, mean and factor R 2
of long-short, the ﬁrst, and the tenth
prediction-weighted decile portfolios that use different information sets for the prediction. We con-
sider four different information sets which combine fund-speciﬁc and stock-speciﬁc characteristics
and sentiment. The model predictions are generated in a rolling way. That is, we use data until
year to generate predictions for year t + 1 , with t varying.

Fig. A.25.  This ﬁgure shows the predicted abnormal returns (in percentages) as a function of one fund characteristic conditional on different sentiment
quantiles. The other variables are set to their median. The neural network model is estimated with fund-speciﬁc characteristics and sentiment. When the
training data is until time t, the interaction effects are evaluated on year t + 1 . The ﬁnal interaction measure is averaged across all out-of-sample years.
The high-minus-low portfolios have a higher mean conditional on high past sentiment. This is a non-linear interaction effect.

135

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Fig. A.26.  This ﬁgure shows the importance ranking for individual variables and variable groups. The ranking is the square root of average of the squared
gradient for the eight ensemble ﬁts as in Eq. (7) . When the training data is until time t, the importance measure is on year t + 1 , and the variable
importance measure is averaged across all out-of-sample years. Fund-speciﬁc characteristics and sentiment are used as network input.

Table B.1
Selection of tuning parameters.

Notation

Tuning Parameters

Candidates

Optimal

HL
Number of layers in Neural Network
HU  Number of hidden units in each layer
DR
Dropout
Learning rate
LR
l1 regularization
L1
l2 regularization
L2

1, 2, 3

2 6 −i

or 2 7 −i

, i = 1 to HL

0.90, 0.95
0.001, 0.01
0, 1e-5
0, 1e-2, 1e-3

1
64
0.95
0.01
0
1e-3

This table shows the set of tuning parameters, which result in 144 candidate models. The opti-
mal parameters are selected on the validation data.

rameters, and evaluate the prediction out-of-sample on the
remaining third of the sample. We repeat the estimation
on three different combinations of the three time periods
and report the average results. The estimation and valida-
tion time period is split into 3/4 used for training and 1/4
used for validation to select the optimal tuning parameters
from the candidate set in Table B.1 . For each combination
of candidate tuning parameters we train the network for
512 epochs. Our results are robust to the choice of tuning
parameters as demonstrated in Section IA.4 of the Internet
Appendix. In particular, our results do not depend on the
structure of the network and all models with good perfor-
mance on the validation data provide essentially an identi-
cal model with the same relative performance on the test
data.

The number of layers of the network is a tuning param-
eter selected on the validation data. Theoretically a shal-
low network with few layers but with more nodes can be
equivalent to a deeper network with fewer nodes. Hence, a
discussion about the number of layers needs to be related
to the number of nodes used in each layer. More layers ob-
viously means more parameters to be estimated and there-
fore requires either more data or a stronger signal-to-noise
ratio to be useful. A panel of individual stock returns is a
larger data set and returns–instead of abnormal returns–
seem to have a stronger structure to detect. The data on
abnormal fund returns is comparatively smaller and seems
to have a less complex structure than the data on individ-
ual stock returns. Therefore, the structure that can be esti-
mated robustly in our data seems to be simpler. In conclu-
sion, a smaller number of layers provides a parsimonious
and robust model for our data.

## Appendix C. Variable Importance and Interaction Effects: Statistical Significance Test

We  use  the  large-sample  asymptotic  theory  of
Horel  and  Giesecke  (2020)  to  study  the  statistical
signiﬁcance  of  the  measures  for  Sensitivity (z
k )  and
Interaction (z
k , macro ) . Horel and Giesecke (2020) develop
a  pivotal  test  to  assess  the  statistical  signiﬁcance  of  the
feature  variables  in  a  single-layer  feedforward  neural
network  regression  model.  They  study  the  asymptotics
of  gradient-based  test  statistics  using  nonparametric
techniques.  Using  an  empirical-process  approach,  they
show that the large-sample asymptotic distribution of the
rescaled  neural  network  sieve  estimator  is  given  by  the
argmax of a Gaussian process. A second-order functional
delta method is then used to obtain the asymptotic distri-
bution of the test statistic as the weighted average of the
squared partial derivative of the argmax of the Gaussian
process  with  respect  to  the  variable  of  interest.  They
show  that  a  test  statistics  based  on  the  squared  partial
derivatives can be asymptotically represented by a mixture
of chi-squared distributions.

The asymptotic theory in Horel and Giesecke (2020) is
developed for a one-layer neural network, which is what
we use as the benchmark model in this paper. They apply
their method to univariate partial derivatives, while we ex-
tend it to also measure interaction effects. The functional
delta method arguments directly carry over to our interac-
tion measure, which is simply a linear function of the es-
timated network. We use the same sensitivity measure as
in their paper to study the univariate effects. Their results
are derived for sigmoid basis activation functions, while we

136

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

use ReLU activation function, which can be viewed as an
approximation. This approximation is not expected to af-
fect the empirical distribution results. The functional cen-
tral limit theorems are derived under the assumption that
the samples { R abn
i,t  are i.i.d., which essentially im-
i,t
poses that the error terms from the neural network predic-
tion are independent and identically distributed. Obtaining
a distribution theory for a general estimation approach like
neural networks requires to impose some assumptions of
this form.

i,t , z t }

, z

The  diﬃculty  of  the  procedure  lies  in  obtaining  the
asymptotic  distribution  of  the  neural  network.  Our  im-
plementation  follows  the  “discretization  approach” of
Horel and Giesecke (2020) , which obtains a cover of the
argmax  of  the  Gaussian  process  by  randomly  sampling
neural  networks  which  approximate  the  function  space.
More  speciﬁcally,  we  generate  random  neural  networks
with the same network structure as the benchmark model,
but sample the network parameters randomly.

(cid:5)

1
N t

l (z

N t
i =1 f

(cid:5)
T
t=1

In  more  detail,  we  randomly  sample  M = 10 0 0  func-
tions  f
l  with  the  same  network  structure  as  the  bench-
mark  setup.  The  functions  are  scaled  such  that  the
standard deviation of their predictions is the same as for
the estimated model g(z
i,t ) . In order to generate a sample
from  the  asymptotic  distribution,  we  ﬁrst  generate  a
random sample from a multivariate normal distribution of
dimension M = 10 0 0 with mean 0 and covariance matrix
approximated  by  a  diagonal  matrix  with  diagonal  ele-
ments  1
i,t ) 2 , l = 1 · · · M. T  is the number
T
of periods and N t is the number of funds available at time
t. We extract the maximum index from this multivariate
normal,  l ∗,  and  the  argmax  function  h  is  approximated
by  f
l ∗ ,  we
l ∗ .  Given  the  approximate  argmax  function  f
generate  an  approximate  sample  from  the  asymptotic
k )] 2 =
distribution  of  the  test  statistics:  [ Sensitivity (z
1
Interaction (z,  macro)
and
T
l ∗ ( low z, high macro )) −
= ( f
( f
l ∗ ( low z, low macro )) .  We  re-
peat the process for 10 0 0 times to estimate the quantile
of the test statistics at 1%, 5%, and 10% levels. We obtain
the statistical signiﬁcance levels by comparing the realized
test  statistics  with  the  properly  scaled  quantiles.  The
scaling for Interaction (z, macro) is r n = (  n
)
2(2 d+1)  while
log n
k )] 2  equals  r 2
the  scaling  for  [ Sensitivity (z
n ,  where  n  is
the number of samples and d the number of features in
the  model.  The  scaling  constants  are  different  because
k )] 2 is a squared function, while Interaction (z,
[ Sensitivity (z
macro) is linear.

∂ f
(cid:5)
l ∗ (z
i,t )
N t
T
(
t=1
∂z
i =1
i,k,t
l ∗ ( high z, high macro ) − f

l ∗ ( high z, low macro ) − f

1
N t

d+1

) 2

(cid:5)

This approach is computationally eﬃcient and less ex-
pensive than a bootstrap approach. The partial derivative
underpinning the test statistic is basically a byproduct of
the  widely  used  gradient-based  ﬁtting  algorithms  and  is
provided  by  standard  software  packages  used  for  ﬁtting
neural networks. The test procedure does not require re-
ﬁtting the neural network. Furthermore, the test is not sus-
ceptible to the non-identiﬁability of neural networks.

137

## Supplementary material

Supplementary material associated with this article can
be found, in the online version, at 10.1016/j.jﬁneco.2023.07.
004 .

## References

Akbas, F., Ay, L., Koch, P., 2023. The evolution of market eﬃciency over the

past century. Available at SSRN 4373735.

Amihud, Y., Ruslan, G., 2013. Mutual fund’s R2 as predictor of perfor-

mance. Rev. Financ. Stud. 26 (3), 667–694 .

Baker, M., Wurgler, J., 2006. Investor sentiment and the cross-section of

stock returns. J. Finance 61 (4), 1645–1680 .

Barber, B.M., Huang, X., Odean, T., 2016. Which factors matter to in-
vestors? Evidence from mutual fund ﬂows. Rev. Financ. Stud. 29 (10),
2600–2642 .

Ben-David, I., Li, J., Rossi, A., Song, Y., 2022. What do mutual fund in-

vestors really care about? Rev. Financ. Stud. 35 (4), 1723–1774 .

Berk, J.B., Green, R.C., 2004. Mutual fund ﬂows and performance in ratio-

nal markets. J. Polit. Economy 112 (6), 1269–1295 .

Berk, J.B., Van Binsbergen, J.H., 2015. Measuring skill in the mutual fund

industry. J. Financ. Econ. 118 (1), 1–20 .

Berk, J.B., Van Binsbergen, J.H., 2016. Assessing asset pricing models using

revealed preference. J. Financ. Econ. 119 (1), 1–23 .

Bianchi, D., Büchner, M., Hoogteijling, T., Tamoni, A., 2021. Corrigendum:
bond risk premiums with machine learning. Rev. Financ. Stud. 34 (2),
1090–1103 .

Bianchi, D., Büchner, M., Tamoni, A., 2021. Bond risk premiums with ma-

chine learning. Rev. Financ. Stud. 34 (2), 1046–1089 .

Bollen, N., Jeffrey, B., 2005. Short-term persistence in mutual fund perfor-

mance. Rev. Financ. Stud. 18 (2), 569–597 .

Brown, D.P., Wu, Y., 2016. Mutual fund ﬂows and cross-fund learning

within families. J. Finance 71 (1), 383–424 .

Bryzgalova, S., Pelger, M., Zhu, J., 2021. Forest through the trees: Building

cross-sections of stock returns. Working paper.

Carhart, M.M., 1997. On persistence in mutual fund performance. J. Fi-

nance 52 (1), 57–82 .

Chen, L., Pelger, M., Zhu, J., 2023. Deep learning in asset pricing. Manage.

Sci. .

Cong, L. W., Feng, G., He, J., He, X., 2022. Asset pricing with panel trees

under global split criteria. Working paper.

Coval, J., Stafford, E., 2007. Asset ﬁre sales (and purchases) in equity mar-

kets. J. Financ. Econ. 86 (2), 479–512 .

Cremers, M., Petajisto, A., 2009. How active is your fund manager? A
new measure that predicts performance. Rev. Financ. Stud. 22 (9),
3329–3365 .

DeMiguel, V., Gil-Bazo, J., Nogales, F. J., Santos, A . A . P., 2023. Machine
learning and fund characteristics help to select mutual funds with
positive alpha. Working paper.

Doshi, H., Elkamhi, R., Simutin, M., 2015. Managerial activeness and mu-

tual fund performance. Rev. Asset Pricing Stud. 5 (2), 156–184 .

Fama, E.F., French, K.R., 1996. Multifactor explanations of asset pricing

anomalies. J. Finance 51 (1), 55–84 .

Fama, E.F., French, K.R., 2010. Luck versus skill in the cross-section of mu-

tual fund returns. J. Finance 65 (5), 1915–1947 .

Feng, G., Giglio, S., Xiu, D., 2020. Taming the factor zoo: a test of new

factors. J. Finance 75 (3), 1327–1370 .

Filippou, I., Rapach, D., Taylor, M. P., Zhou, G., 2022. Exchange rate pre-
diction with machine learning and a smart carry portfolio. Working
Paper.

Freyberger,  J.,  Neuhierl,  A.,  Weber,  M.,  2020.  Dissecting  charac-
teristics  nonparametrically.  The  Rev.  Financ.  Stud.  33  (5),
2326–2377 .

Gabaix, X., Koijen, R. S., 2021. In search of the origins of ﬁnancial ﬂuctua-

tions: The inelastic markets hypothesis. Working Paper.

Gallaher, S. T., Kaniel, R., Starks, L. T., 2009. Advertising and mutual funds:

From families to individual funds. Working Paper.

Giglio, S., Maggiori, M., Stroebel, J., Utkus, S., 2021. Five facts about beliefs

and portfolios. Am. Econ. Rev. 111 (5), 1481–1522 .

Goodfellow, I., Bengio, Y., Courville, A., 2016. Deep Learning. MIT Press .
Green, J., Hand, J.R., Zhang, X.F., 2017. The characteristics that provide in-
dependent information about average us monthly stock returns. Rev.
Financ. Stud. 30 (12), 4389–4436 .

R. Kaniel, Z. Lin, M. Pelger et al.

Journal of Financial Economics 150 (2023) 94–138

Gruber, M., 1996. Another puzzle: The growth of actively managed mutual

funds. J. Finance 51 (3), 783–810 .

Gu, S., Kelly, B.T., Xiu, D., 2020. Empirical asset pricing via machine learn-

ing. Rev. Financ. Stud. 33 (5), 2223–2273 .

Kosowski, R., 2011. Do mutual funds perform when it matters most to
investors? US mutual fund performance and risk in recessions and
expansions. Q. J. Finance 1 (3), 607–664 .

Kozak, S., Nagel, S., Santosh, S., 2020. Shrinking the cross section. J. Financ.

Haddad, V., Kozak, S., Santosh, S., 2020. Factor timing. Rev. Financ. Stud.

Econ. 135 (2), 271–292 .

33 (5), 1980–2018 .

Hanson, S.G., Sunderam, A., 2014. The growth and limits of arbitrage: ev-
idence from short interest. Rev. Financ. Stud. 27 (4), 1238–1286 .
Horel, E., Giesecke, K., 2020. Towards explainable ai: signiﬁcance tests for

neural networks. J. Mach. Learn. Res. . forthcoming

Ibert, M., Kaniel, R., Van Nieuwerburgh, S., Vestman, R., 2018. Are mutual
fund managers paid for investment skill? Rev. Financ. Stud. 31 (2),
715–772 .

Jegadeesh, N., Mangipudi, C.S., 2021. What do fund ﬂows reveal about as-
set pricing models and investor sophistication? Rev. Financ. Stud. 34
(1), 108–148 .

Jegadeesh, N., Titman, S., 1993. Returns to buying winners and selling
losers:  implications  for  stock  market  eﬃciency.  J.  Finance  48  (1),
65–91 .

Kacperczyk, M., Sialm, C., Zheng, L., 2005. On the industry concentra-
tion  of  actively  managed  equity  mutual  funds.  J.  Finance  60  (4),
1983–2011 .

Kacperczyk, M., Sialm, C., Zheng, L., 2008. Unobserved actions of mutual

funds. Rev. Financ. Stud. 21 (6), 2379–2416 .

Lettau, M., Pelger, M., 2020. Factors that ﬁt the time-series and cross-sec-

tion of stock returns. Rev. Financ. Stud. 33 (5), 2274–2325 .

Li, B., Rossi, A. G., 2021. Selecting mutual funds from the stocks they hold:

a machine learning approach. Working Paper.

Lou, D., 2012. A ﬂow-based explanation for return predictability,. Rev. Fi-

nanc. Stud. 25 (6), 3457–3489 .

Massa, M., Yadav, V., 2015. Investor sentiment and mutual fund strategies.

J. Financ. Quant. Anal. 50 (4), 699–727 .

Moskowitz, T.J., 20 0 0. Mutual fund performance: an empirical decomposi-
tion into stock-picking talent, style, transactions costs, and expenses.
discussion. J. Finance 55, 1695–1703 .

Roussanov, N., Ruan, H., Wei, Y., 2021. Marketing mutual funds. Rev. Fi-

nanc. Stud. 34 (6), 3045–3094 .

Roussanov, N. L., Ruan, H., Wei, Y., 2022. Mutual fund ﬂows and perfor-

mance in (imperfectly) rational markets?Working Paper.

Sadhwani, A., Giesecke, K., Sirignano, J., 2020. Deep learning for mortgage

risk ∗. J. Financ. Econom. 19 (2), 313–368 .

Sapp,  T.,  Tiwari,  A.,  2004.  Does  stock  return  momentum  explain  the

“smart money” effect? J. Finance 59 (6), 2605–2622 .

Kacperczyk, M., Van Nieuwerburgh, S., Veldkamp, L., 2014. Time-varying

Song, Y., 2020. The mismatch between mutual fund scale and skill. J. Fi-

fund manager skill. J. Finance 69 (4), 1455–1484 .

Kacperczyk, M., Van Nieuwerburgh, S., Veldkamp, L., 2016. A rational
theory of mutual funds’ attention allocation. Econometrica 84 (2),
571–626 .

Karolyi, G.A., Van Nieuwerburgh, S., 2020. New methods for the cross-sec-

tion of returns. Rev. Financ. Stud. 33 (5), 1879–1890 .

Kelly, B.T., Pruitt, S., Su, Y., 2019. Characteristics are covariances: a uniﬁed

model of risk and return. J. Financ. Econ. 134 (3), 501–524 .

Koijen, R.S., Yogo, M., 2019. A demand system approach to asset pricing. J.

Polit. Economy 127 (4), 1475–1515 .

nance 75 (5), 2555–2589 .

Stambaugh, R.F., 2014. Presidential address: investment noise and trends.

J. Finance 69 (4), 1415–1453 .

Stambaugh, R.F., Yu, J., Yuan, Y., 2012. The short of it: investor sentiment

and anomalies. J. Financ. Econ. 104 (2), 288–302 .

Wu, W., Chen, J., Yang, Z., Tindall, M.L., 2021. A cross-sectional machine
learning approach for hedge fund return prediction and selection.
Manage. Sci. 67 (7), 4577–4601 .

Zheng, L., 1999. Is money smart? A study of mutual fund investors’ fund

selection ability. J. Finance 54, 901–933 .

138

