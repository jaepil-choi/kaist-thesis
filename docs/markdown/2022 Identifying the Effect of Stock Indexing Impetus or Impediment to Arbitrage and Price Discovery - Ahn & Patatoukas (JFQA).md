# Identifying the Effect of Stock Indexing: Impetus or Impediment to Arbitrage and Price Discovery

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

JOURNAL OF FINANCIAL AND QUANTITATIVE ANALYSIS Vol. 57, No. 5, Aug. 2022, pp. 2022–2062
© The Author(s), 2021. Published by Cambridge University Press on behalf of the Michael G. Foster
School of Business, University of Washington. This is an Open Access article, distributed under the
terms of the Creative Commons Attribution licence (http://creativecommons.org/licenses/by/4.0/), which
permits unrestricted re-use, distribution, and reproduction in any medium, provided the original work is
properly cited.
doi:10.1017/S0022109021000235

Identifying the Effect of Stock Indexing:
Impetus or Impediment to Arbitrage and
Price Discovery?

Byung Hyun Ahn
University of California, Berkeley, Haas School of Business
byunghyun_ahn@haas.berkeley.edu

Panos N. Patatoukas
University of California, Berkeley, Haas School of Business
panos@haas.berkeley.edu (corresponding author)

## Abstract

The rise of stock indexing has raised concerns that index investing impedes arbitrage and
degrades price discovery. This article uses Russell’s reconstitution to identify the causal
effect of index investing on information arbitrage and price discovery. Although index
investing has no discernible effect on the ability of arbitrageurs to trade and impound news
into the prices of large- and mid-cap stocks, we find that index investing increases the speed
of price adjustment to news for micro-cap stocks. Our causal evidence identifies the relax-
ation of arbitrage constraints as a mechanism through which indexing facilitates informed
trading for more arbitrage-constrained micro-cap stocks.

## I. Introduction

What is the effect of stock indexing on information arbitrage and the efficacy
of the price-discovery process? Forty-three years after John C. Bogle, the Vanguard
Group founder, launched the world’s first index mutual fund on Aug. 31, 1976, and
over 26 years after the debut of the first index exchange-traded fund (ETF) on
Jan. 22, 1993, index investing continues to grow. According to the Investment
Company Institute (ICI), the share of index funds in the fund market more than

We thank FTSE Russell’s Client Service associates and regional managers, especially Mallory
Denney, for providing the Russell 3000E index constituent data and index reconstitution market-cap
breakpoints. We thank FactSet and its research staff for providing the institutional ownership data. We
thank Sebastian Calonico for helpful advice with regression discontinuity design (RDD) applications.
We also thank an anonymous referee, Jennifer Conrad (the editor), John Core, Omri Even-Tov, Kimmie
George, Marc Painter, Jacob Ma-Weaver, Mike Wilkins, and the PhD students at Berkeley Haas for
helpful comments and discussions. We gratefully acknowledge financial support from the Center for
Financial Reporting and Management at Berkeley Haas.

2022

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2023

doubled from 18% in 2009 to 38% in 2019 (e.g., ICI (2020)). At year-end 2019,
total net assets in index funds reached $8.4 trillion, with a 50-50 split between index
mutual funds and index ETFs (ICI (2020)).

The rise of stock indexing has reshaped the investment landscape by democ-
ratizing access to low-cost passive strategies. Yet, it has also raised concerns that the
ascent of index investing distorts stock prices.1 The conventional argument is that
indexing is akin to free-riding on other people’s research because index investors
rely on prices without contributing to price discovery. The substitution of active
investors with index investors, the argument goes, impedes price discovery and
reduces price efficiency. Another related argument is that basket trading, that is,
the mass buying or selling of index constituents, leads to excess comovement
(e.g., Sullivan and Xiong (2012), Da and Shive (2018)), amplifies return volatility
(e.g., Krause, Ehsani, and Lien (2014), Ben-David, Franzoni, and Moussawi
(2018)), and decreases stock liquidity as a result of higher adverse selection costs
(e.g., Hamm (2014), Israeli, Lee, and Sridharan (2017)). This argument implies that
index investing increases the cost and risk of information arbitrage, thereby reduc-
ing price efficiency.

Whereas the critics often argue that indexing hinders informational efficiency,
indexing can facilitate information arbitrage and promote price discovery. First,
there is evidence that higher index ownership leads to enhanced public information
production by analysts and managers (e.g., Boone and White (2015)). Second,
index products provide efficient means to risk transferring and hedging. In fact,
arbitrageurs routinely use index products as building blocks for active strategies
that allow them to bet more aggressively on firm-specific information while hedg-
ing out systematic exposure (e.g., Easley, Michayluk, O’Hara, and Putniņš (2020),
Huang, O’Hara, and Zhong (2020), and Li and Zhu (2019)). In addition, indexing
can improve arbitrageurs’ ability to take short positions and exploit inefficiencies.
This is because index funds control a large portion of the inventory of lendable
stocks and typically participate in securities lending programs (e.g., D’Avolio
(2002), Nagel (2005)). Indeed, low-cost index funds actively use stock loan fees
generated from such programs to enhance fund performance and offset fees for index
investors (e.g., Blocher and Whaley (2015), Prado, Saffi, and Sturgess (2016)).2

The premise that price efficiency decreases with the cost of information
arbitrage dates back to Grossman and Stiglitz (1980). Within the context of their
noisy rational expectations model, a decrease in the cost of information arbitrage
increases price informativeness. With respect to the effect of short-sales constraints

1The fear of indexing may be overblown. Beyond active funds, there are several other active
investors in financial markets, including hedge funds, pension funds, life insurance companies, and
individuals. Despite the significant growth of index investing over the past decade, index funds remain
relatively small investors in the U.S. stock markets. At year-end 2019, index funds held 15% of the value
of U.S. stocks, active funds held another 15%, and other investors held the remaining 70% (ICI (2020)).
2For example, Vanguard has an active approach to stock lending dubbed “value lending” that is
designed to capture a scarcity premium found in hard-to-borrow stocks (Vanguard Group (2018)).
Across index fund managers, there is variation in the structure of securities lending programs and
fee-split arrangements with investors. Whereas Vanguard returns all stock lending proceeds to the
Vanguard funds, Blackrock retains 20%–28.5% for itself, depending on the fund (e.g., “ETFs’ Hidden
Source of Return—Securities Lending” by L. Braham, Barron’s, Apr. 7, 2018).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2024 Journal of Financial and Quantitative Analysis

on price efficiency, Diamond and Verrecchia (1987) propose a rational expectations
model whereby the dominant effect of short-sales constraints is to eliminate more
informative trades and reduce the speed of price adjustment to news. A prediction of
their model is that relaxing short-sales constraints improves stock liquidity as a
result of lower adverse-selection costs and increases the speed of price adjustment
to news. The ideal experimental setting for testing Diamond and Verrecchia’s
(1987) prediction would identify an exogenous source of variation in the severity
of short-sales constraints and examine changes in stock liquidity and the speed of
price adjustment to news before and after the change.

This article aims to identify the causal effect of indexing on arbitrage condi-
tions and price discovery. Sorting out causation from association is an important
issue in the ongoing debate surrounding the rise of index investing. Building on
Chang, Hong, and Liskovich’s (2015) regression discontinuity approach, we use
FTSE Russell’s index reconstitution as a source of exogenous variation in index
investing. This quasi-natural experimental setting tackles head-on the endogeneity
issue in the relation of index investing with informational efficiency. Simply put,
the issue is that stocks with different levels of index fund ownership may differ
along dimensions that are endogenously related to stock liquidity, the severity of
short-sales constraints, and the overall efficacy of the price-discovery process.
The endogeneity issue confounds association studies on the effect of changes in
index investing on outcome variables of interest. An association study would rely
on observables to control for forces that simultaneously determine index investing
and outcome variables, but without being able to rule out the role of correlated
omitted variables and reverse causality.3

The Russell reconstitution process follows a set of rules based on market-cap
breakpoints and a transparent timeline. Each year on the May rank day, FTSE
Russell sorts in descending order all eligible stocks based on market cap. The
largest 4,000 eligible stocks constitute the Russell 3000E index. Stocks ranked
#1 to #1,000 constitute the Russell 1000, and stocks ranked #1,001 to #3,000
constitute the Russell 2000. The #1,000 breakpoint separates large- and mid-cap
Russell 1000 stocks from small-cap Russell 2000 stocks (upper cutoff). The #3,000
breakpoint separates Russell 3000E micro-cap stocks from Russell 2000 small-cap
stocks (lower cutoff). Because companies cannot precisely manipulate their May-
rank-day market cap to place themselves on either side of the cutoff, the reconsti-
tution creates exogenous variation in end-of-June index membership, when the
reconstituted Russell indexes go into effect.

With respect to indexing, Chang et al. (2015) point out that the Russell 2000
is a relatively more popular benchmark among index institutions than either the
Russell 1000 or the Russell 3000E. With more money tracking Russell 2000 stocks

3A longstanding literature examines the stock price effects of Standard & Poor’s (S&P) 500 index
inclusions (e.g., Shleifer (1986), Harris and Gurel (1986), Vijh (1994), and Barberis, Shleifer, and
Wurgler (2005)). Different from the Russell indexes, which are rules based, the S&P 500 constituents
are selected by a committee of members of the S&P Dow Jones Indexes’ staff. According to the S&P’s
methodology (see https://www.spglobal.com/spdji/en/indices/equity/sp-500/#overview),
the S&P
500 index does not simply contain the 500 largest stocks; rather, it covers leading companies
from leading industries. The black-box nature of the S&P 500 selection does not allow for a quasi-
experimental design similar to that in the Russell setting.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2025

relative to otherwise-similar stocks at the reconstitution cutoffs, small and random
differences in their May-rank-day market cap cause discontinuous changes in index
ownership due to forced buying and selling of stock additions and deletions around
the reconstitution cutoffs. Stocks added to the Russell 2000, either by dropping
below the #1,000 breakpoint or by rising above the #3,000 breakpoint, will expe-
rience a discontinuous increase in index ownership due to forced buying by tracking
institutions. Stocks deleted from the Russell 2000, either by rising above the #1,000
breakpoint or by dropping below the #3,000 breakpoint, will experience a discon-
tinuous decrease in index ownership due to forced selling by tracking institutions.
To estimate the effect of stock indexing, we implement a regression discon-
tinuity design (RDD) and zero in on changes in outcomes before and after the
Russell reconstitution. The RDD builds on the idea that stocks near the reconsti-
tution cutoff are similar except with respect to their index membership and takes
advantage of the fact that small and random differences in May-rank-day market
cap cause large and discontinuous changes in index investing at the end of June.
First, we validate that the Russell reconstitution leads to discontinuous changes in
the fraction of shares held by index institutions. Then, we identify the treatment
effects for stock additions and deletions relative to counterfactual stocks that could
have been added to or deleted from the Russell 2000 if their May-rank-day market
cap were only slightly different.

The RDD reveals stark differences at the #3,000 breakpoint vis-à-vis the
#1,000 breakpoint. Although our estimates imply that exogenous variation in index
investing has no discernible effects at the upper cutoff separating large- and mid-cap
stocks from small-cap stocks, we find significant treatment effects at the lower
cutoff separating small- from micro-cap stocks. Micro-cap stock additions to
the Russell 2000 experience a discontinuous relaxation of securities lending con-
straints, an improvement in liquidity, and an increase in synchronicity, as well as an
increase in the speed of price adjustment to market, industry, and firm news. On the
flip side, micro-cap stock deletions from the Russell 2000 experience a discontin-
uous tightening of securities lending constraints, a deterioration in liquidity, and a
decrease in synchronicity, as well as a decrease in the speed of price adjustment
to news.

The lack of discernible effects at the upper cutoff and the evidence of signif-
icant effects for micro-cap stock additions and deletions at the lower cutoff of the
Russell 2000 offer a new perspective on the effect of indexing. In cross-sectional
tests, we further explore variation in the addition effects at the lower cutoff with pre-
reconstitution characteristics, including the intensity of arbitrage constraints and a
stock’s information environment. The evidence shows that an exogenous increase
in index investing facilitates the timelier incorporation of news, especially for
stocks that are harder to borrow and harder to trade prior to their reconstitution
into the Russell 2000. This finding highlights the relaxation of arbitrage constraints
as a mechanism through which an exogenous increase in index investing enables
more informed trading and improves price discovery.

Overall, the evidence is consistent with the premise that indexing can facilitate
information arbitrage and increase price efficiency for more arbitrage-constrained
micro-cap stocks. Prior research often interprets evidence of higher price synchro-
nicity as de facto evidence of a deteriorating information environment and more

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2026 Journal of Financial and Quantitative Analysis

noise in prices (e.g., Hamm (2014), Israeli et al. (2017)). In contrast, our evidence
from micro-cap stock additions at the lower cutoff of the Russell 2000 shows that
higher price synchronicity due to an exogenous increase in index investing reflects
the earlier resolution of uncertainty through the timelier incorporation of news
rather than a decrease in price informativeness.

We acknowledge that causality does not automatically translate into general-
izability. The RDD estimates may not be representative of treatment effects that
would occur further away from the cutoffs (e.g., Cattaneo, Idrobo, and Titiunik
(2017)). Nevertheless, our sensitivity analyses show that RDD estimates are robust
to alternative bandwidths around the Russell reconstitution cutoffs. Although our
article is silent with respect to the welfare implications of indexing, Chabakauri
and Rytchkov (2021) analytically demonstrate that investors are better off in an
economy with indexing than in a pre-indexing economy.

Our article is related to prior association studies providing mixed results on the
effect of passive ownership changes. Israeli et al. (2017) find that increases in ETF
ownership are associated with a weaker relation between stock returns and future
earnings, which they interpret as evidence of a deterioration in long-run informa-
tional efficiency due to lower stock liquidity and less informed trading. Glosten,
Nallareddy, and Zou (2021) find that increases in ETF ownership are associated
with a stronger relation between stock returns and contemporaneous earnings,
which they interpret as an improvement in short-run informational efficiency
due to stronger responsiveness to common information across stocks. Bhojraj,
Mohanram, and Zhang (2020) provide evidence that sector-ETF membership is
associated with a stronger earnings–return relation as a result of stronger respon-
siveness to industry and idiosyncratic information, whereas broad-ETF mem-
bership is associated with a weaker earnings–return relation as a result of weaker
responsiveness to market information. Different from prior association studies,
our article provides new evidence on the causal effect of index investing on
arbitrage conditions, price synchronicity, and the speed of price adjustment to
market, industry, and firm news.

Our article is also related to that by Coles, Heath, and Ringgenberg (2020).
Like our article, they use the Russell reconstitution to identify the effect of exog-
enous variation in index investing. Unlike our article, they focus exclusively on the
upper cutoff of the Russell 2000. Whereas Coles et al. conclude that index investing
does not affect price efficiency, our article yields a much more nuanced under-
standing of the effect of indexing on the price-discovery process and presents novel
evidence regarding which stocks are and are not affected and, most importantly,
why. At the upper cutoff, we find that index investing has no discernible effect on
the ability of arbitrageurs to trade and impound news into the prices of large- and
mid-cap stocks. At the lower cutoff, however, we find strong evidence that index
investing facilitates informed trading and increases the speed of price adjustment to
news for micro-cap stocks, particularly those that are more arbitrage constrained
(i.e., stocks that are more illiquid and harder to borrow). Our evidence shows that
exogenous variation in index investing is impactful at the lower cutoff of the
Russell 2000 because micro- and small-cap stocks are significantly more arbi-
trage constrained relative to mid- and large-cap stocks at the upper cutoff of the
Russell 2000.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2027

Our article demonstrates how researchers can use the Russell reconstitution
as a source of exogenous variation in index investing not only at the upper cutoff,
separating large- and mid-cap stocks from small-cap stocks, but also at the lower
cutoff, separating small- from micro-cap stocks. In this regard, our application is
related to Cao, Gustafson, and Velthuis’s (2019) article on the effect of index
membership on small firm financing. Our evidence further highlights the economic
significance of the lower cutoff as an important experimental setting. An overarch-
ing implication for future research is that unless there is strong motivation to focus
exclusively on either the upper or the lower cutoff, researchers need to consider the
effect of variation in index investing at both reconstitution cutoffs.

## II. Research Design

### A. The Annual Russell Reconstitution

FTSE Russell’s U.S. equity indexes are designed to represent the investable
opportunity set in the U.S. market, and the annual reconstitution process is key to
maintaining an accurate representation of the investable stocks. The Russell recon-
stitution follows a set of rules based on market-cap breakpoints and a transparent
timeline.

Table 1 reports the timeline of the annual Russell reconstitution between 2007
and 2016. The reconstitution event dates are available from FTSE Russell’s Client
Service. May is the ranking month. On the May-rank day, FTSE Russell sorts, in
descending order, all eligible stocks based on their total market cap at the close and
determines the breakpoints between large- and mid-cap stocks as well as small- and
micro-cap stocks. During our sample period, the rank day consistently falls on the
last trading day at the end of May. The largest 4,000 eligible stocks become the
Russell 3000E index. If there are fewer than 4,000 eligible stocks, then the Russell
3000E includes all eligible stocks.4

TABLE 1

Annual Russell Reconstitution Timeline

Table 1 reports the timeline of the annual Russell reconstitution between 2007 and 2016. The reconstitution event dates are
available from FTSE Russell’s Client Service.

Year

2007
2008
2009
2010
2011
2012
2013
2014
2015
2016

Ranking Day

May 31, Thu.
May 30, Fri.
May 29, Fri.
May 28, Fri.
May 31, Tue.
May 31, Thu.
May 31, Fri.
May 30, Fri.
May 29, Fri.
May 27, Fri.

Reconstitution Day

June 22, Fri.
June 27, Fri.
June 26, Fri.
June 25, Fri.
June 24, Fri.
June 22, Fri.
June 28, Fri.
June 27, Fri.
June 26, Fri.
June 24, Fri.

Effective Date

June 25, Mon.
June 30, Mon.
June 29, Mon.
June 28, Mon.
June 27, Mon.
June 25, Mon.
July 01, Mon.
June 30, Mon.
June 29, Mon.
June 27, Mon.

4Only common stocks listed on eligible U.S. exchanges that pass FTSE Russell’s investability rules
(e.g., total market cap > $30 million, rank-day closing stock price > $1, float > 5% of shares outstanding)
are considered for inclusion in the U.S. indexes; see “Russell U.S. Equity Indexes: Construction and
Methodology” (https://research.ftserussell.com/products/downloads/Russell-US-indexes.pdf).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2028 Journal of Financial and Quantitative Analysis

Prior to the 2007 reconstitution, stocks ranked #1 to #1,000 were included in
the Russell 1000, and stocks ranked #1,001 to #3,000 were included in the Russell
2000. Starting with the 2007 reconstitution, FTSE Russell uses a banding policy for
existing index members that mitigates index turnover around the #1,000 break-
point. The banding policy works as follows: Stocks that were previously in the
Russell 2000 (1000) are moved to the Russell 1000 (2000) only if their market cap is
sufficiently larger (smaller) than that of stock #1,000 (#1,001). If a constituent falls
within a þ= (cid:2) 2:5% band around the percentile rank corresponding to the #1,000
breakpoint, the stock maintains its prior index assignment. The banding policy
shifts the cutoff for prior Russell 2000 (1000) members crossing to Russell 1000
(2000) to the left (right) of the #1,000 breakpoint. Over our sample period, prior
Russell 1000 (2000) members would typically need to cross just below (above)
stock #1,226 (#833) to be added to (deleted from) Russell 2000. The banding policy
does not affect the assignment of newly eligible index members because it only
applies to prior index constituents. In addition, the banding policy does not affect
index assignments at the #3,000 breakpoint because it only applies to the #1000
breakpoint. As a result of banding, index turnover is significantly higher at the
lower cutoff relative to the upper cutoff of the Russell 2000.

June is the transition month. During this month, FTSE Russell communicates to
the marketplace the preliminary and updated lists of projected additions and deletions
for its indexes. The newly reconstituted indexes go into effect after market close on
the last Friday in June. The annual Russell reconstitution day is a highly anticipated
market event, and the last Friday in June is one of the busiest trading days of the year
because of stock index rebalancing.5 Whereas FTSE Russell ranks stocks based on
their May-rank-day market cap to determine index memberships, the reconstituted
Russell indexes weight stocks by their end-of-June float-adjusted market cap. The
float-adjusted index weights shift less (more) liquid stocks toward the bottom (top) of
each index, with the objective of minimizing tracking costs for index funds. FTSE
Russell determines the float-adjusted market cap using only the free-floating
shares available to the public, which excludes shares that are not part of the
investable set (e.g., shares not listed on an exchange, shares held by insiders, etc.).

### B. Sample Construction

We obtain Russell 3000E index constituent data for each annual reconstitution
between 2007 and 2016 from FTSE Russell’s Client Service. Our sample starts with
the 2007 reconstitution because this is the first year with comprehensive coverage
of securities-lending-market data from Markit. The post-2007 period overlaps with
FTSE Russell’s post-banding period and ensures consistency in the reconstitution
process around the upper cutoff of the Russell 2000. In addition, the analysis of
index turnover at the lower cutoff of the Russell 2000 is only possible post-2006.
This is because the Russell 3000E index, which includes the largest 4,000 stocks
and allows us to identify index turnover around the #3,000 breakpoint, is not

5See, for example, “Russell Rebalancing Brings Frenzy to a Summer Friday: Surge in Trading
Expected as Stocks Added to and Dropped from U.S. Benchmarks” by A. Loder, The Wall Street
Journal, June 27, 2019 (https://www.wsj.com/articles/russell-rebalancing-brings-frenzy-to-a-summer-
friday-11561636806).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2029

TABLE 2

Russell 1000/2000 Market-Cap Breakpoints

Panel A of Table 2 reports the end-of-May total market-cap breakpoints ($millions) for the Russell 1000/2000 indexes between
2007 and 2016. We obtain the actual market-cap breakpoints before rounding directly from FTSE Russell’s Client Service.
Panel B reports the counts and aggregate end-of-May market cap ($millions) of additions and deletions at the #3,000 and
#1,000 breakpoints of the Russell 2000 index.

Panel A. End-of-May Total Market-Cap Breakpoints

Year

2007
2008
2009
2010
2011
2012
2013
2014
2015
2016

Russell 1000 Index

Russell 2000 Index

Largest

Smallest

Smallest with Band

Largest with Band

Largest

Smallest

$468,519.1
$468,980.7
$338,407.9
$283,061.3
$411,180.4
$540,213.4
$422,091.7
$545,254.2
$750,547.0
$549,659.6

$2,484.5
$2,008.0
$1,237.7
$1,742.9
$2,224.0
$1,956.0
$2,551.8
$3,087.2
$3,385.2
$2,853.4

$2,353.1

$1,798.4
$1,363.2
$829.2
$1,256.1
$1,624.4
$1,354.5
$1,822.3
$2,199.9
$2,426.8
$1,977.7

$1,665.2

$3,152.2
$2,750.8
$1,687.7
$2,273.5
$2,971.5
$2,607.5
$3,298.1
$4,053.5
$4,307.4
$3,860.1

$3,096.2

$2,477.1
$2,000.1
$1,235.9
$1,733.8
$2,224.0
$1,950.6
$2,551.8
$3,080.0
$3,384.0
$2,851.7

$2,348.9

$261.8
$166.7
$78.3
$111.9
$130.3
$100.7
$128.9
$168.7
$176.7
$132.9

$145.7

Mean

$477,791.5

Panel B. Index Turnover

#1,000 Breakpoint

#3,000 Breakpoint

Additions

Deletions

Additions

Deletions

Year

2007
2008
2009
2010
2011
2012
2013
2014
2015
2016

Mean

No. of
Obs.

Market Cap
($millions)

No. of
Obs.

Market Cap
($millions)

No. of
Obs.

Market Cap
($millions)

No. of
Obs.

Market Cap
($millions)

9
40
43
16
25
30
27
29
49
52

32

$14,026.7
$35,670.5
$24,015.2
$14,963.5
$32,528.8
$28,804.6
$36,857.1
$52,787.6
$84,252.1
$69,624.4

$39,353.0

17
45
45
26
36
40
30
29
28
35

$64,060.5
$172,525.4
$95,292.3
$70,697.8
$133,030.1
$117,213.0
$122,696.7
$147,113.4
$150,248.0
$156,388.5

114
211
224
112
104
127
68
58
75
133

33.1

$122,926.6

122.6

$42,525.1
$53,602.8
$26,916.4
$21,018.0
$23,558.8
$19,976.7
$16,992.5
$14,772.0
$22,384.3
$24,894.3

$26,664.1

167
141
94
139
87
82
86
124
135
89

114.4

$34,203.9
$17,366.5
$5,494.3
$11,651.1
$8,307.2
$5,787.9
$8,081.4
$15,710.3
$16,785.6
$8,386.5

$13,177.5

available until June 2005.6 The RDD focuses on changes in outcome variables from
the year before to the year after each annual reconstitution. Therefore, our data set
effectively covers the period between the end of June of 2006 and the end of May of
2017. Appendix A provides the variable definitions.

Panel A of Table 2 reports the end-of-May market-cap breakpoints between
2007 and 2016. Starting with the Russell 1000, the average market cap of the
smallest Russell 1000 stock without banding is $2.35 billion, which corresponds
to the #1,000 breakpoint. Newly eligible index members with an end-of-May
market cap at or above this cutoff will be included in the Russell 1000 at the end
of June. The average market cap of the smallest Russell 1000 stock with banding is
$1.67 billion, which corresponds to the lower band of the #1,000 breakpoint. Prior
Russell 1000 index members with an end-of-May market cap just below this cutoff
will be added to the Russell 2000 at the end of June.

Turning to the Russell 2000, the average market cap of the largest Russell 2000
stock with banding is $3.1 billion, which corresponds to the upper band of the

6Chang et al. (2015) make a similar observation in their Internet Appendix (http://www.columbia.

edu/~hh2679/InternetAppendixApril2014.pdf).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2030 Journal of Financial and Quantitative Analysis

#1,000 breakpoint. Prior Russell 2000 stocks with an end-of-May market cap above
this cutoff will be deleted from the Russell 2000 and will be added to the Russell
1000 at the end of June. The average market cap of the largest Russell 2000 stock
without banding is $2.35 billion, which corresponds to the #1,001 breakpoint.
Newly eligible index members with an end-of-May market cap at or just below
this cutoff will be included in the Russell 2000 at the end of June. The average
market cap of the smallest Russell 2000 stock is $145.7 million, which corresponds
to the #3,000 breakpoint. Recall that the banding policy applies only at the #1,000
breakpoint, and therefore, at the #3,000 breakpoint, there is only a single cutoff
value. Newly eligible or prior index members with an end-of-May market cap at or
just above this cutoff value will be included in both the Russell 2000 and the Russell
3000E, and those that were just below will be included in only the Russell 3000E.
Panel B of Table 2 reports the counts of stock additions and deletions at the
reconstitution cutoffs of the Russell 2000 between 2007 and 2016. We note that
the counts are conditioned on prior index membership, thereby excluding additions
of newly eligible stocks such as IPOs. On average, index turnover is 3.5 times
higher at the lower cutoff relative to the upper cutoff. This asymmetry is driven by
Russell’s post-2007 banding policy, which is designed to moderate index turnover
at the upper cutoff but not at the lower cutoff. Because of the asymmetry in index
turnover, the aggregate significance of stock additions at the lower cutoff is dis-
proportionately large relative to the size of individual stocks.

### C. Instrument for Index Assignment Variable

The Russell reconstitution process creates index membership discontinuities.
With respect to the #3,000 breakpoint, the reconstitution process creates a single
discontinuity. With respect to the #1,000 breakpoint, the banding policy creates two
discontinuities at the lower and upper bands of the #1,000 breakpoint. The true
index assignment variable, that is, FTSE Russell’s end-of-May market cap ranking,
should perfectly predict end-of-June index membership. FTSE Russell, however,
uses a proprietary measure of total market capitalization and does not provide the
end-of-May market cap rankings.

To construct an instrument for the unobservable index assignment variable, we
start with the reconstituted Russell 3000E list available from FTSE Russell’s Client
Service at the end of June. For each constituent, we measure the end-of-May market
cap by multiplying the closing price on the rank day by the number of shares
outstanding at the company level. Following Chang et al. (2015), we obtain the
number of shares as of the most recent earnings report date prior to the rank day
from Compustat and multiply this number by the CRSP factor to adjust shares for
any corporate distribution after the fiscal quarter ends and before the rank day. We
also obtain shares from CRSP as of the rank day and calculate the total market cap
using the larger of Compustat and CRSP shares.

We sort all Russell 3000E constituents in descending order from largest to
smallest based on their end-of-May total market cap. Then, we generate market-cap
rankings relative to the Russell 1000/2000 market-cap breakpoints. We center the
market-cap rankings at each cutoff (zero ranking). Positive (negative) rankings iden-
tify stocks ranked below (above) the cutoff. We note that the historical market-cap

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2031

breakpoints available online from FTSE Russell’s website are rounded.
This rounding is a source of error in the relative market-cap rankings, especially
for stocks close to the index breakpoints. To improve the strength of our instrument
for the index assignment variable, we obtain the raw (i.e., before-rounding) values
of the market-cap breakpoints directly from FTSE Russell’s Client Service. Panel A
of Table 2 reports the market-cap ranges between 2007 and 2016.

Our instrument is an indicator variable (τ) for Russell 3000E constituents pre-
dicted to be included in the Russell 2000 at the end of June. We make predictions about
end-of-June index assignments using prior index membership and end-of-May
market-cap rankings. At the lower cutoff, we predict that prior Russell 2000 members
ranked at or just above the #3,000 breakpoint will remain in the Russell 2000, whereas
those ranked below will be deleted from the Russell 2000 and will be included in the
Russell 3000E. We also predict that prior Russell 3000E members ranked at or just
above the #3,000 cutoff will be added to the Russell 2000, and those ranked below will
remain in the Russell 3000E. At the upper band of the #1,000 cutoff, we predict that
prior Russell 2000 members ranked just below the upper band will remain in Russell
2000, whereas those ranked above will be deleted from Russell 2000 and will be
included in the Russell 1000. With respect to the lower band of the #1,000 breakpoint,
we predict that prior Russell 1000 members ranked just below the lower band will be
added to the Russell 2000, and those ranked above will remain in the Russell 1000.
By definition, the true assignment variable, that is, FTSE Russell’s end-of-
May market-cap ranking, will perfectly predict end-of-June index membership. Our
instrument is unlikely to perfectly match the true index assignment variable, and
any differences will lead to imperfect compliance. Some stocks assigned to the
treatment groups may fail to receive the treatment, and some stocks may receive the
treatment despite being assigned to the control groups. Our application of a fuzzy
RDD accounts for imperfect compliance under the assumption that the predicted
treatment status is a very strong instrument for the actual treatment status (strong
instrumental-variables (IV) assumption).

### D. Fuzzy Regression Discontinuity Design

#### 1. Two-Equation System

The fuzzy RDD examines how outcome variables of interest behave around
the reconstitution cutoffs for treatment stocks relative to counterfactual stocks that
could have been added to or deleted from the Russell 2000 if their May-rank-day
market cap were only slightly different. We specify the fuzzy RDD as a 2-stage least
squares (2SLS) system:

(

dit ¼ α0 þ α1τit þ α2rit þ α3τit (cid:3) rit þ uit
3dit (cid:3) rit þ εit,

1dit þ β

2rit þ β

¼ β

þ β

yit

0

where d is the indicator variable for actual Russell 2000 index membership at the
end of June, r is the end-of-May total market-cap ranking centered at the reconsti-
tution cutoff (zero ranking) so that positive (negative) values represent stocks
ranked below (above) the cutoff, τ is the indicator variable for predicted Russell

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2032 Journal of Financial and Quantitative Analysis

2000 index membership, and y is the outcome variable. The linear rank-control
functions in the 2-equation system mitigate the influence of stocks ranked away
from either side of the cutoff so that stocks ranked closest to the cutoff contribute
more to the estimated discontinuity.

The first stage estimates a regression of the actual Russell 2000 index mem-
bership on the predicted index membership. The α1 coefficient on τ measures the
change in the probability of Russell 2000 index membership for stock additions and
deletions near the reconstitution cutoff. If our instrument for the index assignment
variable is a perfect predictor of actual index membership, the probability of Russell
2000 index membership would change exactly from 0% to 100% at the reconsti-
tution cutoff, and the coefficient estimate on τ would be exactly equal to 1; that is,
α1 ¼ 1. The second stage estimates a regression for each outcome variable on the
predicted index assignment from the first stage. The β
1 coefficient on d estimates
the treatment effect for stock additions and deletions near the reconstitution cutoff.
More generally, the β
1 coefficient is defined as the ratio of the difference in expected
outcomes at the cutoff divided by the change in the probability of treatment near
the cutoff (e.g., Lee and Lemieux (2010), Roberts and Whited (2013)).

We implement the fuzzy RDD using Calonico, Cattaneo, and Titiunik’s (2015)
rdrobust software in R. Statistical inferences are based on Calonico, Cattaneo, and
Titiunik’s (2014) heteroscedasticity-robust nearest-neighbor variance estimator.
The rdrobust software does not report R2 statistics. The reason for this omission
is that R2 statistics in the fuzzy RDD setting do not have a meaningful interpretation
(see, e.g., Wooldridge’s (2012) discussion of IV estimation in Chapter 15). Con-
sistent with Chang et al. (2015), we estimate the 2-equation system of the fuzzy
RDD conditioning on prior index membership around each reconstitution cutoff.

#### 2. First-Stage Fuzzy RDD Results

Table 3 reports the first-stage fuzzy RDD results. Consistent with the strong IV
assumption, we find large discontinuities in the predicted index membership at the
Russell reconstitution cutoffs. At the lower cutoff, the results show that the prob-
ability of addition to the Russell 2000 increases by 97% for prior Russell 3000E
members ranked just above the cutoff, and the probability of deletion increases by
96% for prior Russell 2000 members ranked below the cutoff. At the upper cutoff,
the results show that the probability of addition to the Russell 2000 increases by
88% for prior Russell 1000 members ranked just below the lower band of the #1,000
breakpoint, and the probability of deletion from the Russell 2000 increases by 84%
for prior Russell 2000 members ranked above the upper band. Even though com-
pliance is not perfect, the first-stage results show that our instrument for the index
assignment variable is a very strong predictor of actual index assignment.7

7Pei and Shen (2017) examine the validity of the fuzzy RDD in the presence of measurement error in
the assignment variable. Their focus, however, is the case where the noise in the assignment variable
induces extreme attenuation bias to the point that the first-stage discontinuity becomes smooth, thereby
eliminating the source of identification. Pei and Shen (2017) point out that if a significant first-stage
discontinuity exists, a fuzzy RDD can still be applied to identify causal treatment effects despite
measurement error in the assignment variable (see also Battistin, Brugiavini, Rettore, and Weber
(2009)). Clearly, our first-stage results provide strong evidence of first-stage discontinuity at both the
upper and lower cutoffs of the Russell 2000.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2033

TABLE 3

First-Stage Fuzzy RDD

Table 3 reports first-stage fuzzy regression discontinuity design (RDD) results. Panel A reports results for additions and
deletions at the #3,000 breakpoint. Panel B reports results for additions at the lower band of the #1,000 breakpoint and
deletions at the upper band of the #1,000 breakpoint. The t-statistics are based on heteroscedasticity-robust standard errors.
*, **, and *** indicate statistical significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed tests. The sample
period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

τ
t-statistic
Adj. R2
No. of obs.

Panel B. #1,000 Breakpoint

Additions

0.97***

146.09
98.0%
1,733

#3,000 Breakpoint

Deletions

0.96***

106.54
95.7%
1,956

Additions | Lower Band

Deletions | Upper Band

#1,000 Breakpoint

τ
t-statistic
Adj. R2
No. of obs.

0.88***

48.27
92.5%
761

0.84***

55.85
92.4%
1,147

#### 3. Local Randomization at the Reconstitution Cutoff

A prerequisite for the validity of the Russell setting as a quasi-natural exper-
imental setting is that companies near the reconstitution cutoff cannot precisely
manipulate their May-rank-day market cap to place themselves on either side of the
cutoff. If companies have only limited control over the index assignment variable,
observations that end up near but on either side of the cutoff should be similar in
terms of their May-rank-day market cap. In contrast, a discontinuity in the sorting
variable at the cutoff would imply that companies can systematically game the
index-assignment rule, thereby invalidating the RDD (e.g., Bakke and Whited
(2012), Roberts and Whited (2013)). The evidence is consistent with local random-
ization such that companies near the reconstitution cutoff cannot precisely manip-
ulate their May-rank-day market cap to place themselves on either side of the cutoff.
Figure 1 plots end-of-May market-cap values against end-of-May market-cap
rankings around the Russell reconstitution cutoffs across equally spaced bins within
a þ= (cid:2) 200 bandwidth. Graph A of Figure 1 shows that end-of-May market-cap
values decline smoothly, with no discontinuous changes near the #3,000 break-
point. Graph B of Figure 1 repeats the analysis separately for the upper band and
the lower band of the #1,000 breakpoint. The plot shows that end-of-May market
cap values decline smoothly, with no discontinuous jumps or drops near the cutoffs.
In untabulated analysis, we fail to reject the null that the density of the end-of-May
total market cap is continuous at the reconstitution cutoffs using McCrary’s (2008)
test. Table 4 reports the estimated pre-assignment effects for the end-of-May total
market cap. The RDD results confirm that there are no discontinuous breaks in the
end-of-May total market cap of stocks that were added to or deleted from the Russell
2000 relative to the counterfactual stocks.

Table 4 also reports RDD results for the pre-reconstitution change in log total
market cap between the end of June in the prior year and the end of May in the

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2034 Journal of Financial and Quantitative Analysis

FIGURE 1

Continuity in End-of-May Market Cap

Figure 1 presents evidence of continuity in the end-of-May total market cap around the Russell 2000 index reconstitution
cutoffs. Graph A plots end-of-May market-cap values against end-of-May market-cap rankings at the #3,000 breakpoint.
Graph B plots end-of-May market-cap values against end-of-May market-cap rankings at the lower and upper bands of the
#1,000 breakpoint. The sample period is between 2007 and 2016.

Graph A. Lower Cutoff of Russell 2000 Index

)

N
B
$

(

p
a
C

t
e
k
r
a
M
y
a
M

)

N
B
$

(

p
a
C

t
e
k
r
a
M
y
a
M

$0.25

$0.20

$0.15

$0.10

$0.15

$0.00

–200

–150

–100

–50

0

50

100

150

200

May Market Cap Ranking

Graph B. Upper Cutoff of Russell 2000 Index

$5.00

$4.00

$3.00

$2.00

$1.00

$0.00

–200

–150

–100

Lower Band

Upper Band

100

150

200

–50

0
May Market Cap Ranking

50

current year. We skip the window between the end of May and the end of June as the
transition month in the prior year’s reconstitution. The estimated effects for the pre-
reconstitution change in log market cap are indistinguishable from 0. We find the
same result for the pre-reconstitution change in the rank transformation of the total
market cap. The null results imply that there are no systematic differences in the pre-
ranking trajectories of stocks reconstituted in and out of the Russell 2000 relative to
counterfactual stocks that could have been added to or deleted from the index if their
end-of-May market cap were only slightly different. These null results address
Appel, Gormley, and Keim’s (2021) concern that index switching would not be an
exogenous event if the index assignment instrument in the fuzzy RDD is related to
pre-reconstitution movements in the total market cap. Next, we search for pre-
assignment effects on institutional ownership (IO) at the end of March, that is, the
most recent quarter prior to Russell’s reconstitution at the end of June.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2035

Local Randomization at the Russell Reconstitution Cutoffs

TABLE 4

Table 4 reports second-stage fuzzy regression discontinuity design (RDD) results for pre-reconstitution characteristics,
including the end-of-May total market cap, the pre-reconstitution change in total market cap between the end of June in
the prior year and the end of May in the current year, and the end-of-March index institutional ownership (IO) and its
components. Panel A reports results for additions and deletions at the #3,000 breakpoint. Panel B reports results for
additions at the lower band of the #1,000 breakpoint and deletions at the upper band of the #1,000 breakpoint. Statistical
inferences are based on Calonico et al.’s (2014) heteroscedasticity-robust nearest-neighbor variance estimator. *, **, and ***
indicate statistical significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed tests. The sample period is between
2007 and 2016.

Panel A. Pre-Assignment Effects at the #3,000 Breakpoint

End-of-May market cap ($billions)
Δ(log market cap), June to May
Δ(rank market cap), June to May
End-of-March index IO (%)
End-of-March non-index IO (%)
End-of-March total IO (%)

#3,000 Breakpoint

Additions

Deletions

Treatment

0.01
0.04
0.00
(cid:2)0.07
(cid:2)1.08
(cid:2)1.14

z-Stat.

1.40
0.89
0.04
(cid:2)0.27
(cid:2)0.50
(cid:2)0.51

Treatment

0.00
0.00
(cid:2)0.01
0.09
1.14
1.23

z-Stat.

(cid:2)0.33
0.11
(cid:2)0.96
0.24
0.54
0.53

Panel B. Pre-Assignment Effects at the #1,000 Breakpoint

End-of-May market cap ($billions)
Δ(log market cap), June to May
Δ(rank market cap), June to May
End-of-March index IO (%)
End-of-March non-index IO (%)
End-of-March total IO (%)

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

0.03
(cid:2)0.04
0.00
(cid:2)0.06
1.78
1.73

z-Stat.

0.31
(cid:2)0.55
(cid:2)0.15
(cid:2)0.06
0.48
0.43

Treatment

(cid:2)0.04
(cid:2)0.01
0.00
0.32
4.83
5.15

z-Stat.

(cid:2)0.36
(cid:2)0.20
0.14
0.36
1.52
1.47

We measure the index component of institutional ownership (index IO) as the
fraction of shares held by index institutions that report their quarterly holdings on
U.S. Securities and Exchange Commission (SEC) Form 13F and N-30Ds. We
separate index from non-index institutions using FactSet’s Global Ownership
Database. Appendix B provides details on the measurement of index IO. Table 4
shows that stock additions and deletions are like the counterfactual stocks in terms
of the pre-reconstitution level of index ownership. The estimated pre-assignment
effects for index IO are indistinguishable from 0. These null results further help
reassure that evidence of post-reconstitution treatment effects does not reflect
discontinuities in unobservable characteristics (e.g., Roberts and Whited (2013)).8

8Prior articles often use end-of-June Russell index weights instead of end-of-May total-market-cap
values to instrument the index assignment variable (see, e.g., Wei and Young (2021) review). Chang et al.
(2015) warn against this choice as one that would invalidate the RDD for two reasons. First, FTSE
Russell ranks stocks based on their end-of-May total market cap to determine index memberships.
Because end-of-June index weights are based on end-of-June rather than end-of-May closing prices,
stocks are reshuffled because of the June returns. Second, end-of-June weights are based on float-
adjusted market cap, which only includes free-floating shares. The float-adjusted index weights shift less
(more) liquid stocks toward the bottom (top) of each index so that higher-ranked (lower-ranked) stocks in
terms of end-of-May total market cap will end up with lower (higher) end-of-June float-adjusted weights.
In additional analysis, we find significant discontinuities in pre-reconstitution characteristics when we
use end-of-June Russell index weights to instrument the index assignment variable, which violates the
assumption of local randomization and invalidates the RDD.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2036 Journal of Financial and Quantitative Analysis

## III. Identifying the Effect of Stock Indexing

This section presents evidence on the causal effect of stock indexing on
arbitrage conditions and price discovery. We first confirm evidence of forced
buying and selling by tracking institutions near the Russell reconstitution cutoffs.
We then examine the effect of exogenous variation in index investing on securities-
lending-market conditions, liquidity conditions, return synchronicity, and the speed
of price adjustment to news.

### A. Pre-Reconstitution Characteristics

Table 5 reports average pre-reconstitution characteristics for counterfactual
stocks within the þ= (cid:2) 200 bandwidth around the Russell reconstitution cutoffs.
We identify four groups of counterfactual stocks. At the upper (lower) band of the
#1,000 breakpoint, we identify static Russell 2000 (static Russell 1000) stocks that
would have been reconstituted in the Russell 1000 (Russell 2000) if their end-of-
May market cap were slightly higher (lower). On the left (right) of the #3,000
breakpoint, we identify static Russell 2000 (static Russell 3000E) stocks that would
have reconstituted in the Russell 3000E (Russell 2000) if their end-of-May market
cap were slightly lower (higher). Throughout, we quantify the magnitude of the
estimated addition and deletion effects relative to pre-reconstitution average values
of static stock characteristics.

The comparison of pre-reconstitution characteristics highlights that micro-
and small-cap stocks at the lower cutoff of the Russell 2000 are significantly more
arbitrage constrained relative to mid- and large-cap stocks at the upper cutoff of the
Russell 2000. Indeed, static micro-cap stocks have a combination of low index IO,
low lendable quantity, and high inventory concentration, together with high stock
loan fees, high short-selling risk, wider bid–ask spreads, and higher stock illiquidity
ratios. One key insight from this comparison is that exogenous variation in index
investing is more likely to be impactful for stock additions and deletions at the lower
cutoff of the Russell 2000.

### B. The Effect of Stock Indexing on Index and Non-Index Ownership

A key feature of the Russell setting is that small and random differences in
market cap at the end of May can move stocks between indexes and cause discon-
tinuous changes in index investing at the end of June. Table 6 presents the fuzzy
RDD estimates of the treatment effects on IO. Our estimation zeroes in on the
change in the quarterly values of total IO and its components from March (i.e., the
last value available prior to the reconstitution) to September (i.e., the first value
available after the reconstitution).

Panel A of Table 6 reports the estimated addition and deletion effects at
the lower cutoff of the Russell 2000. Starting with stock additions, we find a
discontinuous jump in total IO, which is consistent with forced buying by tracking
institutions. Breaking down total IO, the estimated addition effects show a 3.87-
percentage-point increase in index IO, which corresponds to a 132% increase
relative to the pre-reconstitution average value of static Russell 3000E stocks,
whereas the change in non-index IO is indistinguishable from 0. Turning to stock

TABLE 5

Pre-Reconstitution Characteristics

Table 5 reports the pre-reconstitution mean values of characteristics for counterfactual stocks within a +/–200 bandwidth around the Russell reconstitution cutoffs. The sample period is between 2007 and 2016.

#1,000 Breakpoint

#3,000 Breakpoint

Static Stocks

Russell 2000 (upper band)

Russell 1000 (lower band)

Russell 2000

Russell 3000E

End-of-May market cap ($billions)
Index weight (basis points)
End-of-March index IO (%)
End-of-March non-index IO (%)
End-of-March total IO (%)
Pre-recon lendable quantity (%)
Pre-recon inventory concentration (%)
Pre-recon quantity on loan (%)
Pre-recon stock loan fee (%)
Pre-recon short-selling risk (%)
Pre-recon bid–ask spread (%)
Pre-recon illiquidity ratio (%)
Pre-recon inelasticity ratio (%)
Pre-recon price synchronicity (logit)
Pre-recon systematic volatility (log)
Pre-recon idiosyncratic volatility (log)
Pre-recon market delay (logit)
Pre-recon industry delay (logit)
Pre-recon firm delay (logit)
Pre-recon earnings delay (logit)
Pre-recon negative delay (logit)

2.77
17.65
15.20
70.89
86.10
27.42
16.52
6.78
0.71
0.30
0.10
0.14
2.52
(cid:2)0.68
(cid:2)7.27
(cid:2)6.59
(cid:2)1.84
(cid:2)1.84
(cid:2)1.94
(cid:2)2.58
(cid:2)0.61

1.96
1.04
13.34
70.48
83.82
24.85
17.59
6.54
0.98
0.52
0.12
0.18
2.42
(cid:2)0.79
(cid:2)7.19
(cid:2)6.40
(cid:2)1.76
(cid:2)1.79
(cid:2)1.86
(cid:2)2.22
(cid:2)0.51

0.16
0.92
8.61
42.88
51.49
15.43
23.97
4.13
2.21
0.98
0.45
7.92
10.23
(cid:2)1.51
(cid:2)7.24
(cid:2)5.73
(cid:2)1.05
(cid:2)1.06
(cid:2)1.11
(cid:2)1.33
0.19

0.13
0.06
2.93
35.24
38.17
8.42
37.63
1.03
2.32
1.25
1.20
30.55
23.41
(cid:2)2.47
(cid:2)8.32
(cid:2)5.85
(cid:2)0.08
(cid:2)0.06
(cid:2)0.11
0.49
1.17

A
h
n
a
n
d
P
a
a
o
u
k
a
s

t

t

2
0
3
7

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2038 Journal of Financial and Quantitative Analysis

The Effect of Stock Indexing on Index and Non-Index Ownership

TABLE 6

Table 6 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in institutional ownership from
March (i.e., the last quarterly value available prior to Russell’s reconstitution) to September (i.e., the first quarterly value
available after Russell’s reconstitution). Panel A reports results for additions and deletions at the #3,000 breakpoint. Panel B
reports results for additions at the lower band of the #1,000 breakpoint and deletions at the upper band of the #1,000
inferences are based on Calonico et al.’s (2014) heteroscedasticity-robust nearest-neighbor
breakpoint. Statistical
variance estimator. *, **, and *** indicate statistical significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed
tests. The sample period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)

No. of obs.

Panel B. #1,000 Breakpoint

Δ(INDEX_IO)
Δ(NON_INDEX IO)
Δ(TOTAL_IO)

No. of obs.

#3,000 Breakpoint

Additions

Deletions

Treatment

3.87***
0.29
4.16***

z-Stat.

27.16
0.40
5.43

Treatment

(cid:2)4.31***
0.82
(cid:2)3.49***

z-Stat.

(cid:2)23.60
0.86
(cid:2)3.48

1,707

1,940

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

3.35***

(cid:2)0.31
3.04*

z-Stat.

10.61
(cid:2)0.19
1.78

Treatment

(cid:2)2.91***
(cid:2)0.14
(cid:2)3.04*

z-Stat.

(cid:2)8.98
(cid:2)0.09
(cid:2)1.87

759

1,131

deletions, we find a discontinuous drop in total IO, which is consistent with forced
selling by tracking institutions. Separating index from non-index IO holdings, the
estimated deletion effects show a 4.31-percentage-point decrease in index IO,
which corresponds to a 50% decrease relative to the pre-reconstitution average
value of static Russell 2000 stocks, and an indistinguishable-from-zero change in
non-index IO.

Panel B of Table 6 reports the estimated addition and deletion effects at
the upper reconstitution cutoff of the Russell 2000. Again, consistent with forced
buying and selling activity by tracking institutions, we find significant addition
and deletion effects at the upper cutoff. The treatment effects show a 3.35-
percentage-point increase in index IO for stock additions at the lower band
of the #1,000 breakpoint, which corresponds to a 25% increase relative to the
pre-reconstitution average value of static Russell 1000 stocks, and a 2:91-
percentage-point decrease in index IO for stock deletions at the upper band of
the #1,000 breakpoint, which corresponds to a 19% decrease relative to the pre-
reconstitution average value of static Russell 2000 stocks. Again, the estimated
treatment effects on the non-index component of IO are indistinguishable
from zero.

In summary, we find that small and random differences in the end-of-May
market cap cause large and discontinuous changes in index IO for stock additions
and deletions relative to counterfactual stocks at the Russell reconstitution cutoffs.
Although consistent with prior evidence of forced buying and selling by passive

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2039

The Effect of Stock Indexing on Securities Lending Conditions

TABLE 7

Table 7 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in securities-lending-market
conditions from the year before to the year after the annual Russell reconstitution. Panel A reports results for additions and
deletions at the #3,000 breakpoint. Panel B reports results for additions at the lower band of the #1,000 breakpoint and
inferences are based on Calonico et al.’s (2014)
deletions at the upper band of the #1,000 breakpoint. Statistical
heteroscedasticity-robust nearest-neighbor variance estimator. *, **, and *** indicate statistical significance at the 10%,
5%, and 1% levels, respectively, using 2-tailed tests. The sample period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)

No. of obs.

Panel B. #1,000 Breakpoint

Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)

No. of obs.

#3,000 Breakpoint

Additions

Deletions

Treatment

3.22***
(cid:2)8.52***
1.70***
(cid:2)0.87**
(cid:2)0.62**

z-Stat.

9.98
(cid:2)6.11
6.82
(cid:2)2.13
(cid:2)2.32

Treatment

(cid:2)4.18***
6.13***
(cid:2)1.71***
1.54***
0.34

z-Stat.

(cid:2)10.37
7.61
(cid:2)5.30
2.80
1.23

1,590

1,820

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

2.83***

(cid:2)0.13
1.43*
(cid:2)0.11
0.20

z-Stat.

3.39
(cid:2)0.23
1.67
(cid:2)0.25
0.81

Treatment

(cid:2)1.86***
0.60
(cid:2)0.02
(cid:2)0.03
0.11

z-Stat.

(cid:2)2.79
1.38
(cid:2)0.03
(cid:2)0.09
0.43

720

1,096

institutions tracking the Russell indexes (e.g., Appel, Gormley, and Keim (2016),
(2019), Ben-David et al. (2018), Ben-David, Franzoni, and Moussawi (2019), and
Glossner (2021)), our evidence highlights the relevance of the annual Russell
reconstitution as a source of exogenous variation in index IO at both the upper
and lower cutoffs of the Russell 2000. Our evidence further highlights the impor-
tance of using a thorough measure of index IO when evaluating the overall IO effect
of forced buying and selling by tracking institutions.9

### C. The Effect of Stock Indexing on Securities Lending Conditions

Next, we provide evidence on the effect of stock indexing on securities-
lending-market conditions. Table 7 presents the estimated treatment effects of stock
indexing on securities-lending-market conditions. Our estimates zero in on changes
from the year before to the year after Russell’s reconstitution at the end of June. The
pre-reconstitution window is from the first Wednesday after last year’s reconstitu-
tion day to the last Tuesday before this year’s end-of-May ranking day. The post-
reconstitution window is from the first Wednesday after this year’s reconstitution

9In additional analysis, we find weaker evidence of addition and deletion effects using Bushee’s
(1998) factor-based classification of quasi-indexer institutions (QIX). When compared with FactSet’s
measure of index IO, QIX is a less direct measure of the fraction of shares held by index institutions.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2040 Journal of Financial and Quantitative Analysis

day to the last Tuesday before next year’s end-of-May ranking day. The window
skips June as the transition month in the index reconstitution process.

We obtain daily securities lending data from Markit. Markit aggregates survey
information from institutional lenders that collectively account for most of the
U.S. securities lending market. Our data set includes the quantity of stock inventory
that is available to lend (LENDABLE_QUANTITY) and the quantity of stock
on loan (QUANTITY_ON_LOAN), both expressed as a percentage of the shares
outstanding. Our data set also includes information about stock inventory concen-
tration. Markit’s inventory-concentration score ranges from 0 to 100; a small score
indicates many lenders with low inventory, and a top score indicates a single lender
with all the inventory. To investigate the effect of stock indexing on the borrow cost,
we use Markit’s indicative rate of the standard borrow cost, which is expressed as a
percentage of the stock price. Following Engelberg, Reed, and Ringgenberg (2018),
we use the standard deviation of daily stock loan fees to measure short-selling risk
in the year before and year after Russell’s reconstitution.

Starting with stock additions at the lower reconstitution cutoff, Panel A of
Table 7 provides evidence that exogenous increases in indexing lead to a significant
relaxation of securities lending constraints. The estimated treatment effects show a
3.22-percentage-point increase in lendable quantity, which corresponds to a 38%
increase relative to the pre-reconstitution average value of static Russell 3000E
stocks, accompanied by a significant decrease in inventory concentration across
stock lenders and an increase in the lendable quantity on loan. The evidence
also shows a 0:87-percentage point decrease in stock loan fees and a 0:62-
percentage-point decrease in short-selling risk, as indicated by the discontinuous
drop in the variability of stock loan fees. Turning to stock deletions at the lower
cutoff, we find evidence that exogenous decreases in indexing lead to a significant
tightening of securities lending constraints. The estimated treatment effects show
a 4:18-percentage-point decrease in lendable quantity, which corresponds to a
27% decrease relative to the pre-reconstitution average value of static Russell
2000 stocks, accompanied by a significant increase in inventory concentration, a
decrease in the lendable quantity on loan, and a 1.54-percentage-point increase in
stock loan fees.

With respect to the upper reconstitution cutoff, Panel B of Table 7 shows
that stock additions at the lower band of the #1,000 breakpoint experience a 2.83-
percentage-point increase in lendable quantity, which corresponds to an 11%
increase relative to the pre-reconstitution average value of static Russell 1000
stocks. On the flip side, stock deletions at the upper band of the #1,000 breakpoint
experience a 1:86-percentage-point decrease in lendable quantity, which corre-
sponds to a 7% decrease relative to the pre-reconstitution average value of static
Russell 2000 stocks. In contrast to evidence of significant effects at the lower cutoff,
the estimated effects on inventory concentration, stock loan fee, and short-selling
risk are indistinguishable from 0 at the upper cutoff. These null findings are
consistent with the fact that pre-reconstitution stock lending conditions are signif-
icantly more relaxed at the upper cutoff relative to the lower cutoff. Indeed, the pre-
reconstitution level of lendable quantity, as a percentage of shares outstanding, is
8.42% for micro-cap stocks at the #3,000 breakpoint and 24.85%, nearly 3 times
higher, for mid-cap stocks at the lower band of the #1,000 breakpoint (see Table 5).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2041

FIGURE 2

Pre- and Post-Reconstitution Stock-Lending-Inventory Dynamics: Additions and Deletions
at the Upper and Lower Russell Reconstitution Cutoffs

Figure 2 plots the cumulative change in stock-lending-inventory concentration for additions and deletions at the lower and
upper cutoffs of the Russell 2000 index. The cumulation window is between trading days –250 and +250 relative to the day of
the annual Russell reconstitution at the end of June (day 0). Markit’s measure of inventory concentration ranges from 0 to 100.
A low score indicates many lenders with low inventory, and a top score indicates a single lender with all the inventory. The
bottom (top) solid line presents the cumulative addition (deletion) effect on inventory concentration for stock additions
(deletions) at the lower cutoff of the Russell 2000 relative to the counterfactual static stocks on the right (left) of the #3,000
breakpoint. The dashed (dotted) line presents the cumulative addition (deletion) effect on inventory concentration for stock
additions (deletions) at the upper cutoff of the Russell 2000 relative to the counterfactual static stocks on the left (right) of the
lower (upper) band of the #1,000 breakpoint.

n
o
i
t
a
r
t
n
e
c
n
o
C
y
r
o
t
n
e
v
n

I

n

i

e
g
n
a
h
C
e
v
i
t
a
u
m
u
C

l

12.00

10.00

8.00

6.00

4.00

2.00

0.00

–2.00

–4.00

–6.00

–8.00

–10.00

–12.00

–250

–200

–150

–100

Deletion-Lower Cutoff

Addition-Upper Cutoff

Deletion-Upper Cutoff

Addition-Lower Cutoff

100

150

200

250

–50

0
Days Relative to Reconstitution

50

Figure 2 provides insights into the stock-lending-inventory dynamics from the
year before to the year after Russell’s reconstitution at the end of June (day 0). The
figure plots the cumulative change in Markit’s inventory-concentration score for
additions and deletions at the lower and upper cutoffs of the Russell 2000. The light-
gray (dark-gray) solid line presents the cumulative addition (deletion) effect on
inventory concentration for stock additions (deletions) at the lower cutoff of the
Russell 2000 relative to the counterfactual static stocks on the right (left) of the
#3,000 breakpoint. The light-gray (dark-gray) dashed line presents the cumulative
addition (deletion) effect on inventory concentration for stock additions (deletions)
at the upper cutoff of the Russell 2000 relative to the counterfactual static stocks on
the left (right) of the lower (upper) band of the #1,000 breakpoint.

With respect to the lower reconstitution cutoff, Figure 2 shows a discontinuous
decrease (increase) in inventory concentration for additions (deletions) to the
Russell 2000 in the days following the annual Russell reconstitution. The post-
reconstitution changes are mostly complete within the first trading week after day
0 and persist in the subsequent year. In addition, there is only limited evidence
of pre-reconstitution changes in inventory concentration. Consistent with the
RDD estimates, the figure also shows that there are no discernible pre- and post-
reconstitution effects on stock-lending-inventory concentration for stock additions
and deletions at the upper reconstitution cutoff.

In summary, we find evidence of large and discontinuous changes in securities
lending conditions due to stock indexing. The treatment effects are especially

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2042 Journal of Financial and Quantitative Analysis

pronounced for stock additions and deletions at the lower cutoff of the Russell 2000
because the pre-reconstitution stock-lending-supply constraints are more binding
for micro-cap stocks. The evidence establishes that at the lower cutoff, the Russell
reconstitution is an exogenous source of variation in the severity of shorts-sales
constraints. The relaxation of stock-lending-supply conditions is a mechanism
through which indexing can improve stock liquidity and accelerate the speed of
price adjustment to news. Next, we provide evidence on the effect of stock indexing
on liquidity conditions.

### D. The Effect of Stock Indexing on Liquidity

Table 8 presents the estimated treatment effects of stock indexing on liquidity.
Our estimates zero in on changes in liquidity from the year before to the year after
Russell’s reconstitution at the end of June. Again, the pre-reconstitution window is
from the first Wednesday after last year’s reconstitution day to the last Tuesday
before this year’s end-of-May ranking day, and the post-reconstitution window is
from the first Wednesday after this year’s reconstitution day to the last Tuesday
before next year’s end-of-May ranking day. We skip June as the transition month in
the reconstitution process. Therefore, our results are not skewed by the spike in
share turnover due to rebalancing on the reconstitution day.

We obtain daily information on closing asks and bids from CRSP and measure
the bid–ask spread as the daily spread of the closing ask minus the closing bid
divided by the midpoint. We explore two complementary stock illiquidity ratios.

TABLE 8

The Effect of Stock Indexing on Liquidity Conditions

Table 8 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in liquidity from the year before
to the year after the annual Russell reconstitution. Panel A reports results for additions and deletions at the #3,000 breakpoint.
Panel B reports results for additions at the lower band of the #1,000 breakpoint and deletions at the upper band of the #1,000
breakpoint. Statistical inferences are based on Calonico et al.’s (2014) heteroscedasticity-robust nearest-neighbor variance
estimator. *, **, and *** indicate statistical significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed tests. The
sample period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)

No. of obs.

Panel B. #1,000 Breakpoint

Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)

No. of obs.

#3,000 Breakpoint

Additions

Deletions

Treatment

(cid:2)0.47***
(cid:2)13.28***
(cid:2)8.33***

z-Stat.

(cid:2)7.60
(cid:2)5.08
(cid:2)5.61

Treatment

0.26***
3.34**
2.56***

z-Stat.

8.25
2.51
2.99

1,696

1,933

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

0.00
0.01
(cid:2)0.19

z-Stat.

0.20
0.09
(cid:2)0.49

Treatment

0.00
(cid:2)0.03
(cid:2)0.20

z-Stat.

0.32
(cid:2)0.81
(cid:2)0.63

756

1,127

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2043

First, we use Amihud’s (2002) illiquidity ratio of the absolute value of the daily
stock return divided by the daily dollar trading volume multiplied by 108. Second,
we use Gao and Ritter’s (2010) inelasticity ratio of the absolute value of the daily
stock return divided by the daily share turnover.

With respect to the lower reconstitution cutoff, Panel A of Table 8 provides
evidence that stock indexing has a significant effect on all three measures of liquidity.
Stock additions at the #3,000 breakpoint experience a 0.47-percentage-point decrease
in the bid–ask spread, which corresponds to a 39% decrease relative to the pre-
reconstitution average spread of static Russell 3000E stocks, accompanied by a
significant drop in illiquidity ratios. On the flip side, stock deletions at the #3,000
breakpoint experience a 0.26-percentage-point increase in the bid–ask spread, which
corresponds to a 57% increase relative to the pre-reconstitution average spread of
static Russell 2000 stocks, accompanied by a significant jump in illiquidity ratios.

Turning to the upper reconstitution cutoff, Panel B of Table 8 reports that
the estimated treatment effects on liquidity are indistinguishable from 0. The lack of
evidence of treatment effects at the upper cutoff is consistent with the fact that
liquidity is significantly higher for large- and mid-cap stocks relative to micro-cap
stocks in the pre-reconstitution year. To illustrate, the average pre-reconstitution
bid–ask spread, as a percentage of the midpoint, is 0.12% for mid-cap stocks at the
lower band of the #1,000 breakpoint and 1.20%, 10 times wider, for micro-cap
stocks at the #3,000 breakpoint and (see Table 5).

Figure 3 provides insights into the stock liquidity dynamics from the year
before to the year after Russell’s reconstitution at the end of June (day 0). The figure

Pre- and Post-Reconstitution Stock Liquidity Dynamics: Additions and Deletions
at the Upper and Lower Russell Reconstitution Cutoffs

FIGURE 3

Figure 3 plots the cumulative change in the bid–ask spread for additions and deletions at the lower and upper cutoffs of the
Russell 2000 index. The cumulation window is between trading days –250 and +250 relative to the day of the annual Russell
reconstitution at the end of June (day 0). The light-gray (dark-gray) solid line presents the cumulative addition (deletion) effect
on the bid–ask spread for stock additions (deletions) at the lower cutoff of the Russell 2000 relative to the counterfactual static
stocks on the right (left) of the #3,000 breakpoint. The dashed (dotted) line presents the cumulative addition (deletion) effect on
the bid–ask spread for stock additions (deletions) at the upper cutoff of the Russell 2000 relative to the counterfactual static
stocks on the left (right) of the lower (upper) band of the #1,000 breakpoint.

d
a
e
r
p
S
k
s
A
-
d
B
n

i

i

e
g
n
a
h
C
e
v
i
t
a
u
m
u
C

l

0.70

0.50

0.30

0.10

–0.10

–0.30

–0.50

–0.70

–250

–200

–150

–100

Deletion-Lower Cutoff

Addition-Upper Cutoff
Deletion-Upper Cutoff

Addition-Lower Cutoff

100

150

200

250

–50

0
Days Relative to Reconstitution

50

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2044 Journal of Financial and Quantitative Analysis

plots the cumulative change in the bid–ask spread for additions and deletions at the
lower and upper cutoffs of the Russell 2000 relative to counterfactual stocks. With
respect to the lower reconstitution cutoff, the figure shows a discontinuous decrease
(increase) in the bid–ask spread for additions (deletions) to the Russell 2000 in the
days following the annual Russell reconstitution that persists in the subsequent year.
In addition, there is no evidence of pre-reconstitution changes in the bid–ask spread.
Consistent with the RDD estimates, the figure also shows that there are no discern-
ible pre- and post-reconstitution effects on the bid–ask spread for stock additions
and deletions at the upper reconstitution cutoff.

We hasten to note that our evidence on the effect of exogenous variation in
index investing on stock liquidity differs from the association evidence of Israeli
et al. (2017). Whereas their article finds that increases in ETF ownership are
associated with lower stock liquidity, we provide causal evidence that an exogenous
increase in index investing i) does not hurt liquidity for stock additions at the upper
cutoff and ii) improves liquidity for stock additions at the lower cutoff of the Russell
2000 index.

### E. The Effect of Stock Indexing on Price-Synchronicity and Volatility

Components

Next, we provide evidence on the effect of stock indexing on stock price
synchronicity and volatility. We measure price synchronicity for each firm in the
year before and after the index reconstitution as the R2 from the following regres-
sion of weekly firm returns (ri,w,t) on the contemporaneous market returns (rm,w,t)
and industry returns (rj,w,t):

ri,w,t ¼ αit þ β

itrm,w,t þ γ

itrj,w,t þ εi,w,t:

(cid:2)

We compute weekly returns from Wednesday to Tuesday. The pre-
reconstitution window is from the first Wednesday after last year’s reconstitution
day to the last Tuesday before this year’s end-of-May ranking day, and the post-
reconstitution window is from the first Wednesday after this year’s reconstitution
day to the last Tuesday before next year’s end-of-May ranking day. We measure
market returns using Fama and French’s value-weighted market portfolio. We mea-
sure industry returns using Fama and French’s 12 value-weighted industry portfolios.
Following prior research, we use a logit transformation of the regression
(cid:3)
model R2, that is, log R2=1 (cid:2) R2
. This logit transformation mitigates skewness
and circumvents the bounded nature of the regression model R2within the [0, 1]
interval (e.g., Morck, Yeung, and Yu (2000) and Durnev, Morck, and Yeung (2004)).
We note that i) the R2 is equal to the variance of the systematic component of returns
divided by the variance of total returns, and ii) the variance of total returns is equal to
the variance of systematic returns plus the variance of idiosyncratic returns. It follows
from these two points that the logit transformation of R2 is equal to the log variance of
systematic returns (SYSTEMATIC_VOLATILITY) minus the log variance of idio-
syncratic returns (IDIOSYNCRATIC_VOLATILITY). It follows that the treatment
effect for Δ(PRICE_SYNCHRONICITY) is equal to the effect for Δ(SYSTEMATIC_
VOLATILITY) minus the effect for Δ(IDIOSYNCRATIC_VOLATILITY).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2045

The Effect of Stock Indexing on Price Synchronicity and Volatility

TABLE 9

Table 9 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in price-synchronicity and
stock-return-volatility components from the year before to the year after the annual Russell reconstitution. Panel A reports
results for additions and deletions at the #3,000 breakpoint. Panel B reports results for additions at the lower band of the #1,000
breakpoint and deletions at the upper band of the #1,000 breakpoint. Statistical inferences are based on Calonico et al.’s
(2014) heteroscedasticity-robust nearest-neighbor variance estimator. *, **, and **** indicate statistical significance at the
10%, 5%, and 1% levels, respectively, using 2-tailed tests. The sample period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)

No. of obs.

Panel B. #1,000 Breakpoint

Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)

No. of obs.

#3,000 Breakpoint

Additions

Deletions

Treatment

1.07***
1.15***
0.09

z-Stat.

6.18
5.54
0.80

Treatment

(cid:2)0.64***
(cid:2)0.86***
(cid:2)0.23**

z-Stat.

(cid:2)4.64
(cid:2)5.36
(cid:2)2.43

1,591

1,779

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

0.23
0.39
0.16

z-Stat.

0.97
1.42
0.89

Treatment

(cid:2)0.24
(cid:2)0.27
(cid:2)0.04

z-Stat.

(cid:2)1.23
(cid:2)1.22
(cid:2)0.26

716

1,079

Table 9 presents the estimated treatment effects of stock indexing on price-
synchronicity and volatility components. The fuzzy RDD estimates focus on
changes from the year before to the year after Russell’s reconstitution. With respect
to the upper reconstitution cutoff, the estimated treatment effects of stock additions
and deletions on price-synchronicity and volatility components are all indistin-
guishable from 0. Focusing on the lower reconstitution cutoff, we find that stock
indexing has a significant effect on price synchronicity. Micro-cap stock additions
to the Russell 2000 experience a discontinuous jump in price synchronicity. On the
flip side, stock deletions from the Russell 2000 experience a discontinuous drop in
price synchronicity. Breaking down price synchronicity into changes in systematic
and idiosyncratic volatility, we find that the change in systematic volatility is the
dominant force at play. More specifically, micro-cap stock additions to the Russell
2000 experience a discontinuous jump in systematic volatility, whereas the esti-
mated treatment effect on idiosyncratic volatility is indistinguishable from 0. On the
flip side, stock deletions from the Russell 2000 experience a discontinuous drop in
systematic volatility accompanied by a smaller but significant drop in idiosyncratic
volatility, which partially offsets the overall effect on price synchronicity.

Some prior articles interpret an increase in price synchronicity as indicative of
a deteriorating information environment whereby less firm-specific information is
incorporated in prices (e.g., Durnev et al. (2004), Chan and Hameed (2006)). Other
studies, however, take the opposite view and interpret higher price synchronicity as
indicative of a lower level of uncertainty that remains unresolved (e.g., Ali, Hwang,
and Trombley (2003), Zhang (2006)). Within the context of our article, the question

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2046 Journal of Financial and Quantitative Analysis

is whether the increase in price synchronicity for stock additions at the lower cutoff
reflects the earlier resolution of uncertainty through the timelier incorporation of
news rather than a decrease in stock price informativeness. To address this question,
we next provide evidence on the effect of stock indexing on the speed of price
adjustment to news.

### F. The Effect of Stock Indexing on the Speed of Price Adjustment to News

To investigate the effect of indexing on the speed of price adjustment to news,
we compute different variants of Hou and Moskowitz’s (2005) market-delay mea-
sure for each firm in the year before and after the index reconstitution. We compute
MARKET_DELAY as 1 minus the ratio of the R2 from the regression of weekly
firm returns on contemporaneous market and industry returns over the R2 from the
regression of weekly firm returns on contemporaneous market and industry returns
and 4 lags of market returns. Intuitively, the MARKET_DELAY measure captures
the fraction of variation in weekly firm returns explained by lagged market returns.
The higher the value of the measure, the stronger is the delay in response to
market news.

Along the lines of Hou and Moskowitz’s (2005) market-delay measure, we
compute INDUSTRY_DELAY as 1 minus the ratio of the R2 from the regression of
weekly firm returns on contemporaneous market and industry returns over the R2
from the regression of weekly firm returns on contemporaneous market and indus-
try returns and 4 lags of industry returns. The INDUSTRY_DELAY measure
captures the fraction of variation in weekly firm returns explained by lagged
industry returns; the higher its value, the stronger is the delay in response to industry
news. We compute FIRM_DELAY as 1 minus the ratio of the R2 from the regres-
sion of weekly firm returns on contemporaneous market and industry returns over
the R2 from the regression of weekly firm returns on contemporaneous market and
industry returns and 4 lags of firm returns. The FIRM_DELAY measure captures
the fraction of variation in weekly firm returns explained by lagged firm returns; the
higher its value, the stronger is the delay in response to firm news.

We also introduce a higher-frequency measure of the speed of price adjustment
to firm news that focuses on quarterly earnings announcements. We compute
EARNINGS_DELAY as 1 minus the ratio of the R2 from the regression of daily
firm returns on contemporaneous market and industry returns over the R2 from the
regression of the daily firm returns on contemporaneous market and industry
returns and 4 lags of firm returns. Our estimation zeroes in on the 20-day trading
window commencing 2 days after each announcement.10 We estimate the earnings-
announcement delay for each firm in the year before and after the reconstitution.
The EARNINGS_DELAY measure captures the fraction of variation in daily firm
returns post–earnings announcement; the higher its value, the stronger is the delay
in response to earnings news.

10We combine information from Compustat and Institutional Brokers’ Estimate System (IBES) to
identify day 0 of the earnings announcements. When the announcement dates differ between Compustat
and IBES, we use the earlier of the two. We shift the earnings announcement by 1 trading day when the
time stamp of the announcement is after trading hours.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2047

The Effect of Stock Indexing on the Speed of Price Adjustment to News

TABLE 10

Table 10 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in price delay from the year
before to the year after the annual Russell reconstitution. Panel A reports results for additions and deletions at the #3,000
breakpoint. Panel B reports results for additions at the lower band of the #1,000 breakpoint and deletions at the upper band of
the #1,000 breakpoint. Statistical inferences are based on Calonico et al.’s (2014) heteroscedasticity-robust nearest-neighbor
variance estimator. *, **, and *** indicate statistical significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed
tests. The sample period is between 2007 and 2016.

Panel A. #3,000 Breakpoint

Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

No. of obs.

Panel B. #1,000 Breakpoint

Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

No. of obs.

#3,000 Breakpoint

Additions

Deletions

Treatment

(cid:2)1.01***
(cid:2)1.00***
(cid:2)0.92***
(cid:2)1.80***
(cid:2)0.95***

z-Stat.

(cid:2)4.96
(cid:2)4.97
(cid:2)4.44
(cid:2)8.73
(cid:2)5.38

Treatment

z-Stat.

0.58***
0.66***
0.71***
1.03***
0.70***

3.30
3.78
3.98
5.99
4.71

1,591

1,779

#1,000 Breakpoint

Additions | Lower Band

Deletions | Upper Band

Treatment

(cid:2)0.32
(cid:2)0.39
(cid:2)0.50
(cid:2)0.29
(cid:2)0.42

z-Stat.

(cid:2)1.02
(cid:2)1.22
(cid:2)1.59
(cid:2)0.84
(cid:2)1.59

Treatment

z-Stat.

0.15
0.03
0.02
0.35
0.09

0.59
0.12
0.10
1.23
0.42

716

1,079

To measure the speed of price adjustment to negative news, we compute
NEGATIVE_DELAY as 1 minus the ratio of the R2 from the regression of weekly
firm returns on contemporaneous market and industry returns over the R2 from the
regression of weekly firm returns on contemporaneous market and industry returns
and 4 lags of negative values of market, industry, and firm returns. We set positive
values of lagged market, industry, and firm returns to 0. By construction, the
NEGATIVE_DELAY measure captures the fraction of variation in weekly firm
returns explained by lagged values of negative returns; the higher its value, the
stronger is the delay in response to negative news.

Table 10 presents the estimated treatment effects of the speed of price adjust-
ment to news. To mitigate skewness, we use logit transformations of the price-delay
Þ. Our estimates zero in on changes
ð
measures, that is log DELAY=1 (cid:2) DELAY
from the year before to the year after Russell’s reconstitution. Starting with the
lower cutoff, we find that stock indexing has a significant effect on the speed of
price adjustment to news. Stock additions (deletions) at the #3,000 breakpoint
experience a discontinuous drop (jump) in price delay with respect to market,
industry, and firm news, as well as with respect to overall negative news. In contrast,
the estimated effects at the upper cutoff imply that there are no discernible addition
or deletion effects on the speed of price adjustment to news.

Prior association articles often interpret evidence of higher price synchronicity
as de facto evidence of a deteriorating information environment and more noise

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2048 Journal of Financial and Quantitative Analysis

in prices (e.g., Hamm (2014), Israeli et al. (2017)). Different from prior research,
our evidence from the lower cutoff of the Russell 2000 implies that higher price
synchronicity due to an exogenous increase in index investing reflects the earlier
resolution of uncertainty through the timelier incorporation of news rather than a
decrease in stock price informativeness.11

### G. Variation with Pre-Reconstitution Characteristics

Focusing on the lower reconstitution cutoff, we group micro-cap stock addi-
tions into more and less arbitrage-constrained partitions based on pre-reconstitution
characteristics. We define as harder-to-borrow stocks those with a below-average
lendable quantity or an above-average stock-inventory concentration, stock loan
fees, or short-selling risk. We define as harder-to-trade stocks those with above-
average bid–ask spreads or above-average illiquidity ratios. We then classify as
more arbitrage-constrained stocks those that are harder to borrow and harder to
trade. We classify the rest of the stocks as less arbitrage constrained. This classi-
fication generates 2 balanced portfolios of stock additions at the lower cutoff of the
Russell 2000. We estimate the conditional addition effects relative to the counter-
factual group of static Russell 3000E micro-cap stocks on the right of the #3,000
breakpoint.12

Table 11 presents the estimated treatment effects on price synchronicity and
delay separately for more and less arbitrage-constrained stock additions at the lower
cutoff of the Russell 2000. The evidence shows that the discontinuous jump in price
synchronicity at the lower reconstitution cutoff is nearly twice as large for more
constrained relative to less constrained stock additions. Breaking down the drivers
of price synchronicity, we confirm that for both addition groups, the jump in
synchronicity is due to a corresponding jump in systematic volatility rather than
a change in idiosyncratic volatility. We also find that the discontinuous drop in price
delay is nearly 2 to 3 times as large for more constrained relative to less constrained
micro-cap additions. The last 2 columns confirm that the differences in the condi-
tional addition effects are significantly different from 0.

Next, we search for variation across partitions of stock additions at the lower
reconstitution cutoff based on pre-reconstitution management earnings guidance
and sell-side analysts’ coverage, two salient characteristics of a stock’s information
environment. We separate stocks with below-median analyst coverage and no
management guidance (stocks with less coverage) from stocks with above-median
analyst coverage and management guidance (stocks with more coverage). This
classification generates 2 balanced portfolios of stock additions at the lower cutoff.
Table 12 presents the conditional addition effects on price synchronicity and delay

11In additional analysis, we confirm that the vast majority of additions (deletions) at the lower cutoff
that experience an increase (a decrease) in synchronicity also experience a decrease (an increase) in price
delay.

12In additional analysis, we split the counterfactual group of static micro-cap stocks based on the pre-
reconstitution intensity of arbitrage constraints. We find that splitting the counterfactual group does not
affect our estimates of the conditional addition effects because the static micro-cap stocks are unaffected
by the Russell reconstitution, regardless of their pre-reconstitution characteristics.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2049

Variation with Pre-Reconstitution Arbitrage Constraints

TABLE 11

Table 11 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in price synchronicity, return
volatility, and price delay from the year before to the year after the annual Russell reconstitution for micro-cap stock additions
at the lower cutoff of the Russell 2000. We partition micro-cap stock additions at the lower cutoff of the Russell 2000 into i) more
arbitrage constrained and ii) less arbitrage constrained based on pre-reconstitution characteristics. We define as harder-to-
borrow stocks those with a below-average lendable quantity or an above-average stock inventory concentration, stock loan
fees, or short-selling risk. We define as harder-to-trade stocks those with above-average bid–ask spreads or above-average
illiquidity ratios. We then classify as more arbitrage-constrained stocks those that are harder to borrow and harder to trade. We
classify the rest of the stocks as less arbitrage constrained. This classification generates 2 balanced portfolios of micro-cap
stock additions at the lower cutoff. We estimate the conditional addition effects relative to the counterfactual group of static
Russell 3000E micro-cap constituents on the right of the #3,000 breakpoint. Statistical inferences are based on Calonico et
al.’s (2014) heteroscedasticity-robust nearest-neighbor variance estimator. *, **, and *** indicate statistical significance at the
10%, 5%, and 1% levels, respectively, using 2-tailed tests. The sample period is between 2007 and 2016.

#3,000 Breakpoint | Additions

Less Constrained að Þ

More Constrained bð Þ

bð Þ (cid:2) að Þ

Treatment

z-Stat.

Treatment

z-Stat.

Difference

z-Stat.

Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

0.74***
0.71***

(cid:2)0.03
(cid:2)0.69***
(cid:2)0.65***
(cid:2)0.46*
(cid:2)1.28***
(cid:2)0.64***

3.66
3.02
(cid:2)0.22
(cid:2)2.81
(cid:2)2.72
(cid:2)1.87
(cid:2)5.43
(cid:2)3.00

1.35***
1.53***
0.18
(cid:2)1.29***
(cid:2)1.31***
(cid:2)1.31***
(cid:2)2.26***
(cid:2)1.23***

6.30
5.79
1.31
(cid:2)5.14
(cid:2)5.36
(cid:2)5.45
(cid:2)9.12
(cid:2)5.75

0.61**
0.82***
0.21
(cid:2)0.60**
(cid:2)0.66**
(cid:2)0.85***
(cid:2)0.98***
(cid:2)0.59**

2.41
2.69
1.35
(cid:2)2.01
(cid:2)2.27
(cid:2)2.91
(cid:2)3.45
(cid:2)2.30

No. of obs.

1,279

1,306

1,591

Variation with Pre-Reconstitution Information Environment

TABLE 12

Table 12 reports second-stage fuzzy regression discontinuity design (RDD) results for changes in price synchronicity, return
volatility, and price delay from the year before to the year after the annual Russell reconstitution for micro-cap stock additions
at the lower cutoff of the Russell 2000. We partition micro-cap stock additions at the lower cutoff of the Russell 2000 into
i) stocks with less coverage and ii) stocks with more coverage based on pre-reconstitution management earnings guidance
and sell-side analysts’ coverage. Specifically, we separate stocks with below-median analyst coverage and no management
guidance (stocks with less coverage) from stocks with above-median analyst coverage and management guidance (stocks
with more coverage). This classification generates 2 balanced portfolios of micro-cap stock additions at the lower cutoff. We
estimate the conditional addition effects relative to the counterfactual group of static Russell 3000E micro-cap constituents on
the right of the #3,000 breakpoint. Statistical inferences are based on Calonico et al.’s (2014) heteroscedasticity-robust
nearest-neighbor variance estimator. *, **, and *** indicate statistical significance at the 10%, 5%, and 1% levels, respectively,
using 2-tailed tests. The sample period is between 2007 and 2016.

#3,000 Breakpoint | Additions

Less Coverage að Þ

More Coverage bð Þ

bð Þ (cid:2) að Þ

Treatment

z-Stat.

Treatment

z-Stat.

Difference

z-Stat.

Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

1.11***
1.26***
0.15
(cid:2)1.14***
(cid:2)1.08***
(cid:2)0.94***
(cid:2)1.99***
(cid:2)1.04***

4.48
4.41
1.16
(cid:2)4.12
(cid:2)3.93
(cid:2)3.42
(cid:2)8.27
(cid:2)4.18

1.01***
1.04***
0.02
(cid:2)0.89***
(cid:2)0.92***
(cid:2)0.88***
(cid:2)1.63***
(cid:2)0.87***

5.36
4.52
0.18
(cid:2)3.89
(cid:2)4.16
(cid:2)3.77
(cid:2)6.24
(cid:2)4.42

(cid:2)0.09
(cid:2)0.22
(cid:2)0.13
0.24
0.16
0.07
0.36
0.17

(cid:2)0.36
(cid:2)0.71
(cid:2)0.82
0.80
0.53
0.22
1.25
0.65

No. of obs.

1,268

1,317

1,591

separately for micro-cap stocks with less and more coverage. Although the condi-
tional addition effects are significant for both micro-cap partitions, we fail to detect
significant differences. The last 2 columns show that the differences in the condi-
tional addition effects are indistinguishable from 0. This null result further

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2050 Journal of Financial and Quantitative Analysis

highlights the relaxation of arbitrage constraints as a mechanism through which an
exogenous increase in index investing facilitates informed trading and promotes
price discovery for more arbitrage-constrained micro-cap stocks.

In summary, our evidence shows that an exogenous increase in index investing
leads to timelier incorporation of systematic and firm news, especially for stocks
that are more arbitrage constrained prior to their reconstitution into the Russell
2000. Viewed as a whole, the evidence is consistent with Diamond and Verrecchia’s
(1987) prediction that an exogenous source of relaxation in the severity of short-
sales constraints improves stock liquidity and increases the speed of price adjust-
ment to news.

### H. Sensitivity Checks

So far, we report results using a +/–200 bandwidth, linear rank controls, and a
uniform kernel function, which equal-weights observations within the bandwidth
around the cutoff. Appendix C reports results using alternative choices for
the kernel function, and the rank-control polynomial order
the bandwidth,
(Tables A1–A4). With respect to the bandwidth choice, we note that the þ= (cid:2)
200 bandwidth is sufficiently wide to capture 60% of index turnover. Appendix C
reports consistent estimates using a þ= (cid:2) 100 bandwidth, which captures 36% of
index turnover. Appendix C also reports consistent results using Imbens and
Kalyanaraman’s (2012) mean squared error (MSE) bandwidth-selection criterion.
As we explain in Section II.D.1, the linear rank-control functions in the fuzzy RDD
mitigate the influence of stocks ranked away from either side of the cutoff so that
stocks ranked closest to the cutoff contribute more to the estimated discontinuity.13
Appendix C reports consistent results using cubic rank-control functions. Appendix
C also reports consistent estimates using a triangular kernel function, which places
more weight on observations near the cutoff. The evidence also shows that the
estimates are not sensitive to the inclusion of year fixed effects.

Throughout, we estimate the fuzzy RDD system conditioning on prior index
membership around the reconstitution cutoff. Our estimation follows Chang
et al.’s (2015) implementation and compares stocks reconstituted in and out of
the Russell 2000 relative to counterfactual stocks near the reconstitution cutoff.
Appel et al. (2021) express concern that conditioning on prior index membership
could introduce bias, and similar to Ben-David et al. (2019), they recommend
estimating the fuzzy RDD system on the full sample of stocks near the reconsti-
tution cutoff without conditioning on prior index assignment. Our inferences are
not sensitive to this alternative estimation. Appendix C reports the results for
the full sample of stocks within the +/–200 bandwidth around the upper and
lower reconstitution cutoffs without conditioning on prior index membership
(Table A5).

13Cattaneo et al. (2017) recommend the use of local linear functions and caution that the use of
higher-order polynomial rank-control functions tends to produce overfitting and yields unreliable results
near boundary points (see also Gelman and Imbens (2019)).

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2051

## IV. Conclusion

We use the annual Russell reconstitution to identify the causal effect of stock
indexing on information arbitrage and price discovery. Although our evidence
shows that exogenous variation in index investing has no discernible effects at the
upper cutoff separating large- and mid-cap stocks from small-cap stocks, we find
significant addition and deletion effects at the lower cutoff separating small- from
micro-cap stocks. Micro-cap stock additions to the Russell 2000 experience a
relaxation of stock lending constraints; an improvement in liquidity; and an
increase in the speed of price adjustment to market, industry, and firm news.
On the flip side, micro-cap stock deletions from the Russell 2000 experience a
tightening of stock lending constraints, a deterioration in liquidity, and a decrease
in the speed of price adjustment to news. The evidence shows that the addition and
deletion effects are especially pronounced at the lower cutoff of the Russell 2000
because the pre-reconstitution arbitrage constraints are more binding for micro-
cap stocks.

Overall, our article provides new evidence on the causal effect of stock
indexing on arbitrage conditions and price discovery. The critics of stock indexing
often argue that index investing leads to excess comovement and reduces price
informativeness. In contrast, our causal evidence shows that index investing facil-
itates informed trading and increases the speed of price adjustment to news for more
arbitrage-constrained micro-cap stocks. To be clear, we do not argue that there is
only a bright side to stock indexing. Moving forward, a growing concern with
respect to stock indexing is the concentration of ownership and voting power
among the “Big 3” index fund managers: Vanguard, BlackRock, and State Street.
The Big 3 dominate the field, with a collective 81% share of index fund assets.
Mr. Bogle, the founder of Vanguard himself, sounded a warning on index funds and
argued that more competition in the indexing field would be a solution to the rising
concentration. Mr. Bogle also acknowledged, however, that the high barriers to
entry prevent new competitors from entering the indexing field.14 The rise of
concentration among the Big 3 is the subject of an ongoing debate regarding the
future of corporate governance.15 Although it might be too early to resolve this
debate, the issue deserves the attention of policy makers (e.g., Bebchuk and Hirst
(2019)). At the same time, policy makers may need to resist a hasty regulatory
response before index fund stewardship is more fully understood (e.g., Fisch,
Hamdani, and Davidoff Solomon (2019)).

14See “Bogle Sounds a Warning on Index Funds” by J. C. Bogle, The Wall Street Journal,

June 27, 2019.

15Heath, Macciocchi, Michaely, and Ringgenberg (2020) argue that indexing weakens corporate
governance because index funds are more likely to cede power to firm management on contentious
issues. Schmidt and Fahlenbrach (2017) propose that index-tracking institutions are less attentive to
managerial actions that are more difficult and costly to monitor, such as merger and acquisition (M&A)
activity and changes in CEO power. Appel et al. (2016) provide evidence that passive mutual funds use
their large voting blocs to exert influence over essential corporate governance structures, including board
independence, removal of poison pills, and equal voting rights for shareholders. In a follow-up article,
Appel et al. (2019) also provide evidence that passive institutional ownership facilitates shareholder
activism by mitigating free-rider problems.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2052 Journal of Financial and Quantitative Analysis

## Appendix A. Variable Definitions

### Institutional Ownership

INDEX_IO: Percentage of shares outstanding held by index institutions. FactSet
analysts separate index from non-index institutions using information from various
sources, including fund managers, prospectuses, factsheets, audited reports, and
fund accounts. Source: FactSet Global Ownership Database.

NON_INDEX_IO: Percentage of shares outstanding held by institutions minus the

percentage of shares outstanding held by index institutions.

TOTAL_IO: Percentage of shares outstanding held by institutions that manage over
$100 million and report their quarterly holdings on SEC Form 13F and N-30Ds.
Source: FactSet Global Ownership Database.

### Securities Lending Conditions

INVENTORY_CONCENTRATION: Markit’s standardized measure of the distribu-
tion of stock inventory. The measure ranges from 0 to 100. A low score indicates
many lenders with low inventory, and a top score indicates a single lender with all
the inventory.

LENDABLE_QUANTITY: Markit’s quantity of stock inventory available to lend as

a percentage of the number of shares outstanding in the company.

QUANTITY_ON_LOAN: Markit’s quantity of stock on loan as a percentage of the

number of shares outstanding in the company.

SHORT_SELLING_RISK: Standard deviation of Markit’s daily stock loan fee in the

year before and year after Russell’s reconstitution.

STOCK_LOAN_FEE: Markit’s indicative rate of the standard borrow cost on a given
day, expressed as a percentage of the stock price. This is a derived rate using
Markit’s proprietary analytics and data set. The calculation uses borrow costs
between agent lenders and prime brokers as well as rates from hedge funds to
produce an indication of the current market rate.

### Stock Liquidity Conditions

BID_ASK_SPREAD: The daily CRSP spread of closing ask minus closing bid

divided by the midpoint available from CRSP.

ILLIQUIDITY_RATIO: Amihud’s (2002) ratio of the absolute daily stock return

divided by the daily dollar trading volume multiplied by 108.

INELASTICITY_RATIO: Gao and Ritter’s (2010) ratio of the absolute daily stock
return divided by the daily share turnover. We measure daily share turnover as the
number of shares traded over the number of shares outstanding in the company.

### Price Synchronicity and Volatility

PRICE_SYNCHRONICITY: R2 from a regression of weekly firm returns on the
contemporaneous weekly market and industry returns. We compute weekly returns
from Wednesday to Tuesday. We measure market returns using Fama and French’s

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

Ahn and Patatoukas 2053

value-weighted market portfolio. We measure industry returns using Fama and
French’s 12 value-weighted industry portfolios. We use a logit transformation to
mitigate skewness.

SYSTEMATIC_ VOLATILITY and IDIOSYNCRATIC_VOLATILITY: The log var-
iance of the systematic (idiosyncratic) portion of weekly firm returns. We measure
the systematic (idiosyncratic) portion of returns as the fitted (residual) values from a
regression of weekly firm returns on contemporaneous market and industry returns.
We compute weekly returns from Wednesday to Tuesday. We measure market
returns using Fama and French’s value-weighted market portfolio. We measure
industry returns using Fama and French’s 12 value-weighted industry portfolios.

### Price Delay

EARNINGS_DELAY: Fraction of variation in daily firm returns post–earnings
announcement, measured as 1 minus the ratio of the R2 from the regression of
daily firm returns on contemporaneous market and industry returns over the R2
from the regression of the daily firm returns on contemporaneous market and
industry returns and 4 lags of firm returns. The post–earnings announcement period
covers the 20-day trading window commencing 2 days after the quarterly earnings
announcement. We combine information from Compustat and IBES to identify day
0 of the quarterly earnings announcements. When the earnings announcement
dates differ between Compustat and IBES, we use the earlier of the two. We shift
the earnings announcement by 1 trading day when the time stamp of the announce-
ment is after trading hours. We measure market returns using Fama and French’s
value-weighted market portfolio. We measure industry returns using Fama and
French’s 12 value-weighted industry portfolios. We use a logit transformation to
mitigate skewness.

FIRM_DELAY: Fraction of variation in weekly firm returns explained by lagged firm
returns, measured as 1 minus the ratio of the R2 from the regression of weekly firm
returns on contemporaneous market and industry returns over the R2 from the
regression of weekly firm returns on contemporaneous market and industry returns
and 4 lags of firm returns. We compute weekly returns from Wednesday to Tuesday.
We measure market returns using Fama and French’s value-weighted market
portfolio. We measure industry returns using Fama and French’s 12 value-weighted
industry portfolios. We use a logit transformation to mitigate skewness.

INDUSTRY_DELAY: Fraction of variation in weekly firm returns explained by
lagged industry returns, measured as 1 minus the ratio of the R2 from the regression
of weekly firm returns on contemporaneous market and industry returns over the R2
from the regression of weekly firm returns on contemporaneous market and
industry returns and 4 lags of industry returns. We compute weekly returns from
Wednesday to Tuesday. We measure market returns using Fama and French’s
value-weighted market portfolio. We measure industry returns using Fama and
French’s 12 value-weighted industry portfolios. We use a logit transformation to
mitigate skewness.

MARKET_DELAY: Fraction of variation in weekly firm returns explained by lagged
market returns, measured as 1 minus the ratio of the R2 from the regression of
weekly firm returns on contemporaneous market and industry returns over the R2
from the regression of weekly firm returns on contemporaneous market and

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2054 Journal of Financial and Quantitative Analysis

industry returns and 4 lags of market returns. We compute weekly returns from
Wednesday to Tuesday. We measure market returns using Fama and French’s
value-weighted market portfolio. We measure industry returns using Fama and
French’s 12 value-weighted industry portfolios. We use a logit transformation to
mitigate skewness.

NEGATIVE_DELAY: Fraction of variation in weekly firm returns explained by
lagged negative returns, measured as 1 minus the ratio of the R2 from the regression
of weekly firm returns on contemporaneous market and industry returns over the R2
from the regression of weekly firm returns on contemporaneous market and
industry returns and 4 lags of negative market, industry, and firm returns. We set
positive values of lagged market, industry, and firm returns to 0. We compute
weekly returns from Wednesday to Tuesday. We measure market returns using
Fama and French’s value-weighted market portfolio. We measure industry returns
using Fama and French’s 12 value-weighted industry portfolios. We use a logit
transformation to mitigate skewness.

## Appendix B. FactSet Institutional Ownership Database

In Appendix B, we measure the index component of institutional ownership (index
IO) as the fraction of shares held by index institutions that report their quarterly holdings
on SEC Form 13F and N-30Ds. We separate index from non-index institutions using
FactSet’s Global Ownership Database. The research staff members at FactSet manually
attribute the index style for an institutional portfolio based on information they receive
directly from fund managers or from the prospectus, factsheets, or auditor reports and
accounts for each fund. Specifically, we extract the IO data via FactSet’s “Percent
Ownership-Grouped Analysis” function (OS_GRP_HLDR_PCTOS). We then specify
the holder type parameter as institutions and group the percentage of holdings by
index and non-index investor type. As of Dec. 2020, FactSet identifies 84 unique
index institutions around the globe.

We note that FactSet analysts identify index holdings at the fund family/institution
level. The aggregation of index holdings at the fund family/institution level rather than
at the fund level introduces noise in the measurement of index IO. This is because
institutions classified as index can also be large fund managers that have many different
fund styles to cater to all types of investors. To illustrate, Vanguard is classified in the
FactSet database as an index institution, and some of the funds in the Vanguard fund
family are not classified as index funds (e.g., Vanguard Growth & Income, Vanguard
Tax Managed Balanced, Vanguard Alternative Strategies, Vanguard Wellington).

## Appendix C. Sensitivity Checks

In this paper, we report fuzzy RDD results using a þ= (cid:2) 200 bandwidth with linear
rank-control functions and a uniform kernel function, which equal-weights observations
within the bandwidth around the Russell reconstitution cutoff. Throughout, we estimate
the 2-equation system of the fuzzy RDD conditioning on prior index membership
around each reconstitution cutoff.

Appendix C reports results using alternative choices for the bandwidth, the kernel
function, and the rank-control polynomial order. With respect to the bandwidth choice,

Ahn and Patatoukas 2055

Appendix C reports consistent estimates using a þ= (cid:2) 100 bandwidth, which captures
36% of all Russell index turnover. We also find consistent estimates using Imbens and
Kalyanaraman’s (2012) MSE bandwidth-selection criterion, which attempts to opti-
mally balance bias and variance. The MSE bandwidth-selection criterion is fully data
driven and does not require a fixed bandwidth choice across specifications. Across
alternative bandwidths, Appendix C reports consistent estimates using a triangular
kernel function, which places more weight on observations near the cutoff, and cubic
(i.e., third-order polynomial) rank-control functions. Local randomization implies that
the assignment to treatment is independent of baseline covariates (e.g., Lee and Lemieux
(2010)). Consistent with local randomization, we report similar estimates after the
inclusion of year fixed effects as baseline covariates.

Tables A1–A4 report fuzzy RDD estimates of addition and deletion effects at the
Russell reconstitution cutoffs for each outcome variable of interest conditioning on prior
index membership. Table A5 reports fuzzy RDD estimates for the full sample of stocks
within the þ= (cid:2) 200 bandwidth around each reconstitution cutoff without conditioning
on prior index membership. All estimates zero in on the change from the year before
to the year after the annual Russell reconstitution. *, **, and *** indicate statistical
significance at the 10%, 5%, and 1% levels, respectively, using 2-tailed tests. The
sample period is between 2007 and 2016. The variables are listed in the order of
appearance in the manuscript. Appendix A provides all variable definitions.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

TABLE A1

#3,000 Breakpoint: Additions

Uniform Kernel Function

Triangular Kernel Function

Year Fixed Effects

Cubic Rank Controls

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)
Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)
Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)
Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

3.87***
0.29
4.16***
3.22***
(cid:2)8.52***
1.70***
(cid:2)0.87**
(cid:2)0.62**
(cid:2)0.47***
(cid:2)13.28***
(cid:2)8.32***
1.07***
1.15***
0.09
(cid:2)1.01***
(cid:2)1.00***
(cid:2)0.92***
(cid:2)1.80***
(cid:2)0.95***

3.79***

(cid:2)0.35

3.43***
3.25***
(cid:2)7.04***
1.87***
(cid:2)1.28**
(cid:2)0.67*
(cid:2)0.48***
(cid:2)14.85***
(cid:2)8.99***
1.21***
1.34***
0.13
(cid:2)1.12***
(cid:2)1.23***
(cid:2)1.09***
(cid:2)1.60***
(cid:2)1.11***

3.95***

(cid:2)0.54

3.77***
3.24***
(cid:2)8.52***
1.71***
(cid:2)1.10**
(cid:2)0.68**
(cid:2)0.49***
(cid:2)14.18***
(cid:2)8.54***
1.07***
1.11***
0.11
(cid:2)1.10***
(cid:2)1.03***
(cid:2)0.93***
(cid:2)1.75***
(cid:2)0.99***

3.87***

(cid:2)0.12

3.75***
3.15***
(cid:2)7.79***
1.80***
(cid:2)0.99**
(cid:2)0.63**
(cid:2)0.47***
(cid:2)14.00***
(cid:2)8.50***
1.08***
1.20***
0.12
(cid:2)0.99***
(cid:2)1.05***
(cid:2)0.93***
(cid:2)1.68***
(cid:2)0.97***

3.85***
0.57
4.41***
3.05***
(cid:2)5.40**
1.70***

(cid:2)1.20*
(cid:2)0.47
(cid:2)0.49***
(cid:2)16.34***
(cid:2)9.54***
1.37***
1.47***
0.11
(cid:2)1.33***
(cid:2)1.53***
(cid:2)1.21***
(cid:2)1.62***
(cid:2)1.29***

3.87***

(cid:2)0.05

3.80***
3.15***
(cid:2)8.44***
1.65***

(cid:2)0.69*
(cid:2)0.63**
(cid:2)0.47***
(cid:2)13.88***
(cid:2)8.50***
1.09***
1.19***
0.10
(cid:2)1.02***
(cid:2)1.04***
(cid:2)0.95***
(cid:2)1.70***
(cid:2)0.97***

3.89***
0.28
4.17***
3.15***
(cid:2)8.22***
1.66***
(cid:2)0.88**
(cid:2)0.64**
(cid:2)0.49***
(cid:2)14.23***
(cid:2)8.83***
1.04***
1.06***
0.02
(cid:2)1.01***
(cid:2)0.99***
(cid:2)0.89***
(cid:2)1.81***
(cid:2)0.93***

3.85***

(cid:2)0.37

3.48***
3.06***
(cid:2)6.55***
1.69***
(cid:2)1.25**
(cid:2)0.69*
(cid:2)0.50***
(cid:2)16.35***
(cid:2)9.85***
1.06***
1.10***
0.04
(cid:2)0.99***
(cid:2)1.11***
(cid:2)0.92***
(cid:2)1.53***
(cid:2)0.98***

3.96***

(cid:2)0.48

3.84***
3.04***
(cid:2)8.41***
1.84***
(cid:2)1.07**
(cid:2)0.69**
(cid:2)0.50***
(cid:2)14.69***
(cid:2)8.88***
1.09***
1.02***
0.07
(cid:2)1.07***
(cid:2)1.03***
(cid:2)1.00***
(cid:2)1.75***
(cid:2)1.03***

3.70***
1.02
4.72**
3.05***

(cid:2)3.55

1.43***

(cid:2)1.70*
(cid:2)0.43
(cid:2)0.46***
(cid:2)15.36***
(cid:2)8.84***
1.61***
1.70***
0.09
(cid:2)1.60***
(cid:2)1.90***
(cid:2)1.42***
(cid:2)1.59***
(cid:2)1.56***

3.89***
1.16
5.06
3.54***

(cid:2)3.98
1.48*
(cid:2)3.09**
(cid:2)0.05
(cid:2)0.55***
(cid:2)14.08*
(cid:2)8.80**
2.11***
2.24***
0.13
(cid:2)2.06***
(cid:2)2.24***
(cid:2)1.93***
(cid:2)1.80***
(cid:2)2.04***

3.79***

(cid:2)0.22

3.68***
2.99***
(cid:2)6.74***
1.94***
(cid:2)1.48**
(cid:2)0.77*
(cid:2)0.47***
(cid:2)14.56***
(cid:2)8.18***
1.20***
1.33***
0.06
(cid:2)1.15***
(cid:2)1.20***
(cid:2)1.16***
(cid:2)1.66***
(cid:2)1.06***

2
0
5
6

J
o
u
r
n
a

l

o

f

i

F
n
a
n
c
a

i

l

a
n
d
Q
u
a
n

t
i
t

a

t
i
v
e
A
n
a
y
s
s

l

i

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

TABLE A2

#3,000 Breakpoint: Deletions

Uniform Kernel Function

Triangular Kernel Function

Year Fixed Effects

Cubic Rank Controls

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)
Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)
Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)
Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

(cid:2)4.31***
0.82
(cid:2)3.49***
(cid:2)4.18***
6.13***
(cid:2)1.71***
1.54***
0.34
0.26***
3.34**
2.56***
(cid:2)0.64***
(cid:2)0.86***
(cid:2)0.23**
0.58***
0.66***
0.71***
1.03***
0.70***

(cid:2)4.40***
0.08
(cid:2)4.32***
(cid:2)4.34***
6.86***
(cid:2)1.51***
1.05
0.52
0.26***
4.17**
3.10**
(cid:2)0.58***
(cid:2)0.79***
(cid:2)0.21*
0.47**
0.59**
0.42*
0.79***
0.57***

(cid:2)4.34***
0.99
(cid:2)3.36***
(cid:2)4.09***
6.11***
(cid:2)1.65***
1.09*
0.15
0.25***
3.56**
2.12**
(cid:2)0.63***
(cid:2)0.87***
(cid:2)0.25***
0.53***
0.62***
0.63***
0.89***
0.66***

(cid:2)4.34***
0.34
(cid:2)4.01***
(cid:2)4.22***
6.44***
(cid:2)1.66***
1.18**
0.25
0.27***
3.75**
2.71***
(cid:2)0.63***
(cid:2)0.87***
(cid:2)0.24**
0.54***
0.64***
0.60***
0.89***
0.65***

(cid:2)4.35***
(cid:2)0.66
(cid:2)5.01***
(cid:2)4.55***
6.58***
(cid:2)1.85***
0.95
0.42
0.28***
5.22**
3.66**
(cid:2)0.70***
(cid:2)0.90***
(cid:2)0.19

0.63**
0.71***
0.71**
0.82***
0.77***

(cid:2)4.36***
0.00
(cid:2)4.35***
(cid:2)4.23***
6.42***
(cid:2)1.66***
1.10**
0.25
0.26***
3.91**
2.65***
(cid:2)0.63***
(cid:2)0.87***
(cid:2)0.24**
0.53***
0.62***
0.62***
0.85***
0.65***

(cid:2)4.28***
0.71
(cid:2)3.57***
(cid:2)4.17***
6.11***
(cid:2)1.71***
1.54***
0.33
0.27***
3.59***
2.66***
(cid:2)0.63***
(cid:2)0.85***
(cid:2)0.22***
0.57***
0.66***
0.72***
1.02***
0.70***

(cid:2)4.35***
(cid:2)0.10
(cid:2)4.45***
(cid:2)4.58***
7.16***
(cid:2)1.82***
1.08
0.52
0.28***
4.62***
3.18***
(cid:2)0.64***
(cid:2)0.90***
(cid:2)0.26**
0.53**
0.64***
0.47**
0.89***
0.63***

(cid:2)4.36***
0.61
(cid:2)3.71***
(cid:2)4.07***
6.46***
(cid:2)1.81***
1.10*
0.26
0.27***
3.44***
2.42***
(cid:2)0.56***
(cid:2)0.88***
(cid:2)0.24***
0.52***
0.64***
0.65***
0.97***
0.70***

(cid:2)4.38***
(cid:2)0.99
(cid:2)5.37***
(cid:2)4.76***
6.62***
(cid:2)2.01***
0.89
0.72
0.33***
7.57**
5.33***
(cid:2)0.83***
(cid:2)0.92***
(cid:2)0.09

0.82**
0.87***
0.96***
0.94***
0.96***

(cid:2)3.89***
1.12
(cid:2)2.77
(cid:2)5.54***
3.51*
(cid:2)2.22***
1.13
1.20**
0.43***
11.11**
6.63**
(cid:2)1.06***
(cid:2)0.88**
0.18
1.05**
1.02**
1.77***
0.81*
1.33***

(cid:2)4.47***
(cid:2)1.51
(cid:2)5.41***
(cid:2)4.76***
7.09***
(cid:2)1.82***
0.73
0.20
0.31***
6.18**
3.98**
(cid:2)0.74***
(cid:2)1.00***
(cid:2)0.18

0.63**
0.72***
0.68***
0.80***
0.77***

A
h
n
a
n
d
P
a
a
o
u
k
a
s

t

t

2
0
5
7

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

TABLE A3

#1,000 Breakpoint, Lower Band: Additions

Uniform Kernel Function

Triangular Kernel Function

Year Fixed Effects

Cubic Rank Controls

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)
Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)
Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)
Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

3.35***

(cid:2)0.31
3.04*
2.83***

(cid:2)0.13
1.43*
(cid:2)0.11
0.20
0.00
0.01
(cid:2)0.19
0.23
0.39
0.16
(cid:2)0.32
(cid:2)0.39
(cid:2)0.50
(cid:2)0.29
(cid:2)0.42

3.62***

(cid:2)1.24
2.37
3.26**
(cid:2)2.87***
2.92**
0.65
0.61
0.00
(cid:2)0.12
(cid:2)0.64
(cid:2)0.08
(cid:2)0.03
0.05
0.04
0.01
(cid:2)0.26
0.20
(cid:2)0.05

3.29***

(cid:2)0.31
2.73*
2.61***

(cid:2)0.19
1.06
0.04
0.49*
0.00
(cid:2)0.08
(cid:2)0.38
0.16
0.32
0.17
(cid:2)0.28
(cid:2)0.31
(cid:2)0.48
(cid:2)0.30
(cid:2)0.30

3.48***

(cid:2)0.35
3.13
3.18***

(cid:2)0.85

2.18**
0.16
0.41
0.01
(cid:2)0.06
(cid:2)0.42
0.15
0.31
0.16
(cid:2)0.27
(cid:2)0.30
(cid:2)0.42
(cid:2)0.06
(cid:2)0.33

4.00***
0.30
4.30
4.38***
(cid:2)2.59***
3.64**
0.57
0.57
0.02
(cid:2)0.19
(cid:2)1.07
0.09
0.19
0.11
(cid:2)0.31
(cid:2)0.22
(cid:2)0.31
0.43
(cid:2)0.23

3.44***

(cid:2)0.49
3.00
2.62***

(cid:2)0.51

1.70**

(cid:2)0.08
0.21
0.01
(cid:2)0.09
(cid:2)0.40
0.15
0.28
0.09
(cid:2)0.17
(cid:2)0.30
(cid:2)0.39
(cid:2)0.21
(cid:2)0.19

3.26***

(cid:2)0.34
2.92*
2.68***

(cid:2)0.11
1.42*
(cid:2)0.15
0.20
0.00
(cid:2)0.01
(cid:2)0.24
0.25
0.36*
0.11
(cid:2)0.35
(cid:2)0.42
(cid:2)0.52*
(cid:2)0.26
(cid:2)0.43*

3.46***

(cid:2)0.73
2.73
2.93**
(cid:2)2.65***
2.96**
0.58
0.64*
(cid:2)0.01
(cid:2)0.13
(cid:2)0.57
0.01
0.04
0.03
(cid:2)0.08
(cid:2)0.14
(cid:2)0.31
0.11
(cid:2)0.13

3.26***

(cid:2)1.01
2.88*
2.64***

(cid:2)0.34
1.15
(cid:2)0.04
0.63*
(cid:2)0.01
(cid:2)0.16
(cid:2)0.25
0.20
0.20
0.11
(cid:2)0.19
(cid:2)0.29
(cid:2)0.41
(cid:2)0.24
(cid:2)0.35

4.16***
0.32
4.48
5.07**
(cid:2)3.93***
5.04**
1.23
0.83
0.05
(cid:2)0.16
(cid:2)0.96
0.16
0.33
0.17
(cid:2)0.30
(cid:2)0.08
(cid:2)0.26
0.84
(cid:2)0.33

3.47*
7.33
10.79
11.94**
(cid:2)0.54
10.70**
3.15
2.59*
0.15*
(cid:2)0.07
0.11
0.69
1.28
0.59
(cid:2)2.07
(cid:2)0.83
(cid:2)0.61
0.92
(cid:2)0.81

3.80***

(cid:2)0.39
4.22
3.81***

(cid:2)1.08
2.51*
0.95
1.17*
0.03
(cid:2)0.10
(cid:2)0.58
0.28
0.44
0.17
(cid:2)0.19
(cid:2)0.26
(cid:2)0.35
(cid:2)0.36
(cid:2)0.40

2
0
5
8

J
o
u
r
n
a

l

o

f

i

F
n
a
n
c
a

i

l

a
n
d
Q
u
a
n

t
i
t

a

t
i
v
e
A
n
a
y
s
s

l

i

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

TABLE A4

#1,000 Breakpoint, Upper Band: Deletions

Uniform Kernel Function

Triangular Kernel Function

Year Fixed Effects

Cubic Rank Controls

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

þ= (cid:2) 200

þ= (cid:2) 100

þ= (cid:2) MSE

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)
Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)
Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)
Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

(cid:2)2.91***
(cid:2)0.14
(cid:2)3.04*
(cid:2)1.86***
0.60
(cid:2)0.02
(cid:2)0.03
0.11
0.00
(cid:2)0.03
(cid:2)0.20
(cid:2)0.24
(cid:2)0.27
(cid:2)0.04
0.15
0.03
0.02
0.35
0.09

(cid:2)2.74***
1.78
(cid:2)0.95
(cid:2)2.57**
0.52
(cid:2)0.70
(cid:2)0.27
(cid:2)0.17
0.00
0.00
0.03
0.04
(cid:2)0.28
(cid:2)0.32
(cid:2)0.41
(cid:2)0.47
(cid:2)0.22
(cid:2)0.08
(cid:2)0.25

(cid:2)2.54***
2.35
2.01
(cid:2)2.60**
0.57
(cid:2)0.75
(cid:2)0.08
(cid:2)0.16
0.00
(cid:2)0.03
(cid:2)0.19
(cid:2)0.07
(cid:2)0.32
(cid:2)0.33
(cid:2)0.36
(cid:2)0.47
(cid:2)0.06
(cid:2)0.12
(cid:2)0.21

(cid:2)2.84***
0.59
(cid:2)2.24
(cid:2)2.08***
0.79
(cid:2)0.21
(cid:2)0.16
(cid:2)0.03
0.00
(cid:2)0.02
(cid:2)0.11
(cid:2)0.11
(cid:2)0.26
(cid:2)0.15
(cid:2)0.06
(cid:2)0.15
(cid:2)0.03
0.18
(cid:2)0.03

(cid:2)2.70***
3.26
0.56
(cid:2)2.55**
0.94
(cid:2)0.18
(cid:2)0.36
(cid:2)0.30
0.00
(cid:2)0.03
0.06
0.20
(cid:2)0.19
(cid:2)0.39
(cid:2)0.81
(cid:2)0.82
(cid:2)0.30
(cid:2)0.27
(cid:2)0.42

(cid:2)2.65***
1.71
(cid:2)1.09
(cid:2)2.30**
0.84
(cid:2)0.34
(cid:2)0.19
(cid:2)0.09
0.00
(cid:2)0.03
0.05
0.06
(cid:2)0.32
(cid:2)0.23
(cid:2)1.45*
(cid:2)1.26*
(cid:2)0.06
(cid:2)0.28
(cid:2)0.14

(cid:2)2.86***
(cid:2)0.07
(cid:2)2.94*
(cid:2)1.83***
0.59
(cid:2)0.03
(cid:2)0.01
0.14
0.00
(cid:2)0.02
(cid:2)0.10
(cid:2)0.10
(cid:2)0.06
0.04
0.03
(cid:2)0.10
(cid:2)0.12
0.21
(cid:2)0.05

(cid:2)2.57***
1.62
(cid:2)0.95
(cid:2)2.03**
0.28
(cid:2)0.40
(cid:2)0.31
(cid:2)0.17
0.01
0.02
0.10
0.17
0.00
(cid:2)0.16
(cid:2)0.50
(cid:2)0.58
(cid:2)0.33
(cid:2)0.17
(cid:2)0.37

(cid:2)2.10***
2.24
1.18
(cid:2)1.72*
0.35
(cid:2)0.43
(cid:2)0.55
(cid:2)0.17
0.01
(cid:2)0.03
(cid:2)0.16
0.11
0.01
(cid:2)0.20
(cid:2)0.51
(cid:2)0.41
(cid:2)0.27
(cid:2)0.16
(cid:2)0.38

(cid:2)2.43**
3.83
1.40
(cid:2)2.73
1.04
0.25
(cid:2)0.16
(cid:2)0.13
0.00
0.01
0.46
0.29
(cid:2)0.31
(cid:2)0.60
(cid:2)1.49*
(cid:2)1.51*
(cid:2)0.53
(cid:2)0.60
(cid:2)0.60

(cid:2)3.22
0.18
(cid:2)3.04
(cid:2)2.94
3.03
2.11
(cid:2)0.19
(cid:2)0.27
(cid:2)0.04
(cid:2)0.03
2.17
1.38
0.35
(cid:2)1.03
(cid:2)4.90**
(cid:2)4.57*
(cid:2)2.72
(cid:2)1.14
(cid:2)1.89

(cid:2)2.89***
5.26
2.43
(cid:2)3.52
0.42
1.46
(cid:2)0.94
(cid:2)0.63
0.00
0.02
0.43
0.38
(cid:2)0.33
(cid:2)0.65
(cid:2)2.74**
(cid:2)2.40**
(cid:2)1.34
(cid:2)0.54
(cid:2)1.4

A
h
n
a
n
d
P
a
a
o
u
k
a
s

t

t

2
0
5
9

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

Full Sample Within þ= (cid:2) 200 Bandwidth around Each Reconstitution Cutoff

TABLE A5

#3,000 Breakpoint

#1,000 Breakpoint | Lower Band

#1,000 Breakpoint | Upper Band

Treatment

z-Stat.

No. of Obs.

Treatment

z-Stat.

No. of Obs.

Treatment

z-Stat.

No. of Obs.

Δ(INDEX_IO)
Δ(NON_INDEX_IO)
Δ(TOTAL_IO)
Δ(LENDABLE_QUANTITY)
Δ(INVENTORY_CONCENTRATION)
Δ(QUANTITY_ON_LOAN)
Δ(STOCK_LOAN_FEE)
Δ(SHORT_SELLING_RISK)
Δ(BID_ASK_SPREAD)
Δ(ILLIQUIDITY_RATIO)
Δ(INELASTICITY_RATIO)
Δ(PRICE_SYNCHRONICITY)
Δ(SYSTEMATIC_VOLATILITY)
Δ(IDIOSYNCRATIC_VOLATILITY)
Δ(MARKET_DELAY)
Δ(INDUSTRY_DELAY)
Δ(FIRM_DELAY)
Δ(EARNINGS_DELAY)
Δ(NEGATIVE_DELAY)

4.06***

(cid:2)0.08

3.99***
3.76***
(cid:2)7.56***
1.75***
(cid:2)1.22***
(cid:2)0.57***
(cid:2)0.36***
(cid:2)7.77***
(cid:2)5.25***
0.78***
0.91***
0.13*
(cid:2)0.72***
(cid:2)0.78***
(cid:2)0.76***
(cid:2)1.38***
(cid:2)0.76***

23.96
(cid:2)0.13
6.20
12.81
(cid:2)8.80
8.58
(cid:2)3.45
(cid:2)2.85
(cid:2)9.92
(cid:2)5.40
(cid:2)6.34
7.13
7.22
1.91
(cid:2)5.52
(cid:2)5.96
(cid:2)5.61
(cid:2)9.80
(cid:2)6.66

3,941
3,941
3,941
3,613
3,613
3,613
3,613
3,613
3,885
3,885
3,885
3,546
3,546
3,546
3,546
3,546
3,545
3,510
3,546

3.40***
0.99
4.39
2.41
2.41
1.56
(cid:2)0.98
1.29
(cid:2)0.04
0.16
(cid:2)1.01
0.68
0.93
0.25
(cid:2)1.07
(cid:2)0.86
(cid:2)0.48
0.23
(cid:2)0.48

3.13
0.23
0.94
1.02
1.23
0.67
(cid:2)0.77
1.28
(cid:2)0.92
0.29
(cid:2)0.98
1.23
1.41
0.62
(cid:2)1.43
(cid:2)1.14
(cid:2)0.63
0.29
(cid:2)0.79

3,952
3,952
3,952
3,788
3,788
3,788
3,788
3,788
3,921
3,921
3,921
3,732
3,732
3,732
3,732
3,732
3,730
3,714
3,732

(cid:2)2.59***
0.07
(cid:2)2.52
(cid:2)1.04
1.15
0.96
0.22
0.49
0.00
(cid:2)0.21
(cid:2)0.7
(cid:2)0.25
(cid:2)0.1
0.15
0.14
(cid:2)0.01
0.41
0.38
0.10

(cid:2)4.39
0.03
(cid:2)0.98
(cid:2)0.90
1.17
0.97
0.49
1.21
(cid:2)0.20
(cid:2)1.57
(cid:2)1.21
(cid:2)0.80
(cid:2)0.27
0.66
0.32
(cid:2)0.03
0.99
0.90
0.28

3,960
3,960
3,960
3,808
3,808
3,808
3,808
3,808
3,936
3,936
3,936
3,751
3,751
3,751
3,751
3,751
3,749
3,722
3,751

2
0
6
0

J
o
u
r
n
a

l

o

f

i

F
n
a
n
c
a

i

l

a
n
d
Q
u
a
n

t
i
t

a

t
i
v
e
A
n
a
y
s
s

i

l

https://doi.org/10.1017/S0022109021000235 Published online by Cambridge University Press

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

## References

Ahn and Patatoukas 2061

Ali, A.; L. S. Hwang; and M. A. Trombley. “Arbitrage Risk and the Book-to-Market Anomaly.” Journal

of Financial Economics, 69 (2003), 355–373.

Amihud, Y. “Illiquidity and Stock Returns: Cross-Section and Time-Series Effects.” Journal of Finan-

cial Markets, 5 (2002), 31–56.

Appel, I. R.; T. A. Gormley; and D. B. Keim. “Passive Investors, Not Passive Owners.” Journal of

Financial Economics, 121 (2016), 111–141.

Appel, I. R.; T. A. Gormley; and D. B. Keim. “Standing on the Shoulders of Giants: The Effect of Passive

Investors on Activism.” Review of Financial Studies, 32 (2019), 2720–2774.

Appel, I. R.; T. A. Gormley; and D. B. Keim. “Identification Using Russell 1000/2000 Index Assign-

ments: A Discussion of Methodologies.” Critical Finance Review, forthcoming (2021).

Bakke, T. E., and T. M. Whited. “Threshold Events and Identification: A Study of Cash Shortfalls.”

Journal of Finance, 67 (2012), 1083–1111.

Barberis, N.; A. Shleifer; and J. Wurgler. “Comovement.” Journal of Financial Economics, 75 (2005),

Battistin, E.; A. Brugiavini; E. Rettore; and G. Weber. “The Retirement Consumption Puzzle: Evidence
from a Regression Discontinuity Approach.” American Economic Review, 99 (2009), 2209–2226.
Bebchuk, L., and S. Hirst. “The Specter of the Giant Three.” Boston University Law Review, 99 (2019),

283–317.

721–741.

Ben‐David, I.; F. Franzoni; and R. Moussawi. “Do ETFs Increase Volatility?” Journal of Finance,

73 (2018), 2471–2535.

Ben‐David, I.; F. Franzoni; and R. Moussawi. “A Note to ‘Do ETFs Increase Volatility?’: An Improved
Method to Predict Assignment of Stocks into Russell Indexes.” NBER Working Paper (2019).
Bhojraj, S.; P. S. Mohanram; and S. Zhang. “ETFs and Information Transfer across Firms.” Journal of

Accounting and Economics, 70 (2020), 101336.

Blocher, J., and R. E. Whaley. “Passive Investing: The Role of Securities Lending.” Working Paper,

Vanderbilt Owen Graduate School of Management (2015).

Boone, A. L., and J. T. White. “The Effect of Institutional Ownership on Firm Transparency and

Information Production.” Journal of Financial Economics, 117 (2015), 508–533.

Bushee, B. J. “The Influence of Institutional Investors on Myopic R&D Investment Behavior.” Account-

ing Review, 73 (1998), 305–333.

Calonico, S.; M. D. Cattaneo; and R. Titiunik. “Robust Nonparametric Confidence Intervals for

Regression-Discontinuity Designs.” Econometrica, 82 (2014), 2295–2326.

Calonico, S.; M. D. Cattaneo; and R. Titiunik. “rdrobust: An r Package for Robust Nonparametric

Inference in Regression-Discontinuity Designs.” R Journal, 7 (2015), 38–51.

Cao, C. M.; M. Gustafson; and R. Velthuis. “Index Membership and Small Firm Financing.” Manage-

ment Science, 65 (2019), 4156–4178.

Cattaneo, M. D.; N. Idrobo; and R. Titiunik. A Practical Introduction to Regression Discontinuity

Designs. Cambridge, UK: Cambridge University Press (2017).

Chabakauri, G., and O. Rytchkov. “Asset Pricing with Index Investing.” Journal of Financial Econom-

ics, 141 (2021), 195–216.

Chan, K., and A. Hameed. “Stock Price Synchronicity and Analyst Coverage in Emerging Markets.”

Journal of Financial Economics, 80 (2006), 115–147.

Chang, Y. C.; H. Hong; and I. Liskovich. “Regression Discontinuity and the Price Effects of Stock

Market Indexing.” Review of Financial Studies, 28 (2015), 212–246.

Coles, J. L.; D. Heath; and M. Ringgenberg. “On Index Investing.” Working Paper, available at https://

papers.ssrn.com/sol3/papers.cfm?abstract_id=3055324 (2020).

D’Avolio, G. “The Market for Borrowing Stock.” Journal of Financial Economics, 66 (2002), 271–306.
Da, Z., and S. Shive. “Exchange Traded Funds and Asset Return Correlations.” European Financial

Management, 24 (2018), 136–168.

Diamond, D. W., and R. E. Verrecchia. “Constraints on Short-Selling and Asset Price Adjustment to

Private Information.” Journal of Financial Economics, 18 (1987), 277–311.

Durnev, A.; R. Morck; and B. Yeung. “Value‐Enhancing Capital Budgeting and Firm‐Specific Stock

Return Variation.” Journal of Finance, 59 (2004), 65–105.

Easley, D.; D. Michayluk; M. O’Hara; and T. J. Putniņš. “The Active World of Passive Investing.”

Review of Finance, 25 (2021), 1433–1471.

Engelberg, J. E.; A. V. Reed; and M. C. Ringgenberg. “Short‐Selling Risk.” Journal of Finance,

73 (2018), 755–786.

Fisch, J. E.; A. Hamdani; and S. D. Solomon. “The New Titans of Wall Street: ATheoretical Framework

for Passive Investors.” University of Pennsylvania Law Review, 168 (2019), 17–72.

h
t
t
p
s
:
/
/
d
o

i
.

.

o
r
g
/
1
0
1
0
1
7
/
S
0
0
2
2
1
0
9
0
2
1
0
0
0
2
3
5
P
u
b

l
i
s
h
e
d
o
n

l
i

n
e
b
y
C
a
m
b
r
i
d
g
e
U
n
i
v
e
r
s
i
t
y
P
r
e
s
s

2062 Journal of Financial and Quantitative Analysis

Gao, X., and J. R. Ritter. “The Marketing of Seasoned Equity Offerings.” Journal of Financial

Economics, 97 (2010), 33–52.

Gelman, A., and G. Imbens. “Why High-Order Polynomials Should Not Be Used in Regression

Discontinuity Designs.” Journal of Business and Economic Statistics, 37 (2019), 447–456.

Glossner, S. “Russell

Index Reconstitutions,

Institutional

Investors, and Corporate Social

Responsibility.” Critical Finance Review, forthcoming (2021).

Glosten, L.; S. Nallareddy; and Y. Zou. “ETF Activity and Informational Efficiency of Underlying

Securities.” Management Science, 67 (2021), 22–47.

Grossman, S. J., and J. E. Stiglitz. “On the Impossibility of Informationally Efficient Markets.”

American Economic Review, 70 (1980), 393–408.

Hamm, S. “The Effect of ETFs on Stock Liquidity.” Working Paper, available at https://papers.ssrn.com/

sol3/papers.cfm?abstract_id=1687914 (2014).

Harris, L., and E. Gurel. “Price and Volume Effects Associated with Changes in the S&P 500 List: New

Evidence for the Existence of Price Pressures.” Journal of Finance, 41 (1986), 815–829.

Heath, D.; D. Macciocchi; R. Michaely; and M. Ringgenberg. “Do Index Funds Monitor?” Review of

Financial Studies, forthcoming (2021).

Hou, K., and T. J. Moskowitz. “Market Frictions, Price Delay, and the Cross-Section of Expected

Returns.” Review of Financial Studies, 18 (2005), 981–1020.

Huang, S.; M. O’Hara; and Z. Zhong. “Innovation and Informed Trading: Evidence from Industry ETFs.”

Review of Financial Studies, 34 (2021), 1280–1316.

Imbens, G., and K. Kalyanaraman. “Optimal Bandwidth Choice for the Regression Discontinuity

Estimator.” Review of Economic Studies, 79 (2012), 933–959.

Investment Company Institute. “Investment Company Fact Book: A Review of Trends and Activities in
the Investment Company Industry.” Available at https://www.ici.org/system/files/attachments/pdf/
2020_factbook.pdf (2020).

Israeli, D.; C. M. Lee; and S. A. Sridharan. “Is There a Dark Side to Exchange Traded Funds?

An Information Perspective.” Review of Accounting Studies, 22 (2017), 1048–1083.

Krause, T.; S. Ehsani; and D. Lien. “Exchange-Traded Funds, Liquidity, and Volatility.” Applied

Financial Economics, 24 (2014), 1617–1630.

Lee, D. S., and T. Lemieux. “Regression Discontinuity Designs in Economics.” Journal of Economic

Literature, 48 (2010), 281–355.

Li, F. W., and Q. Zhu. “Short Selling ETFs.” Working Paper, available at https://papers.ssrn.com/sol3/

papers.cfm?abstract_id=2836518 (2019).

McCrary, J. “Manipulation of the Running Variable in the Regression Discontinuity Design: A Density

Test.” Journal of Econometrics, 142 (2008), 698–714.

Morck, R.; B. Yeung; and W. Yu. “The Information Content of Stock Markets: Why Do Emerging Markets
Have Synchronous Stock Price Movements?” Journal of Financial Economics, 58 (2000), 215–260.
Nagel, S. “Short Sales, Institutional Investors, and the Cross-Section of Stock Returns.” Journal of

Financial Economics, 78 (2005), 277–309.

Pei, Z., and Y. Shen. “The Devil Is in the Tails: Regression Discontinuity Design with Measurement

Error in the Assignment Variable.” Advances in Econometrics, 38 (2017), 455–502.

Prado, M. P.; P. A. Saffi; and J. Sturgess. “Ownership Structure, Limits to Arbitrage, and Stock Returns:
Evidence from Equity Lending Markets.” Review of Financial Studies, 29 (2016), 3211–3244.
Roberts, M. R., and T. M. Whited. “Endogeneity in Empirical Corporate Finance.” In Handbook of
the Economics of Finance, Vol. 2, G. Constantinides, M. Harris, and R. Stulz, eds. Amsterdam,
Netherlands: North Holland (2013).

Schmidt, C., and R. Fahlenbrach. “Do Exogenous Changes in Passive Institutional Ownership Affect
Corporate Governance and Firm Value?” Journal of Financial Economics, 124 (2017), 285–306.
Shleifer, A. “Do Demand Curves for Stocks Slope Down?” Journal of Finance, 41 (1986), 579–590.
Sullivan, R. N., and J. X. Xiong. “How Index Trading Increases Market Vulnerability.” Financial

Analysts Journal, 68 (2012), 70–84.

Vanguard Group. “Under the Hood of Securities-Lending Practices.” Research and commentary (2018).
Vijh, A. M. “S&P 500 Trading Strategies and Stock Betas.” Review of Financial Studies, 7 (1994), 215–251.
Wei, W., and A. Young. “Selection Bias or Treatment Effect? A Re-Examination of Russell 1000/2000

Index Reconstitution.” Critical Finance Review, forthcoming (2021).

Wooldridge, J. M. Introductory Econometrics: A Modern Approach. Mason, OH: South-Western

Cengage Learning (2012).

Zhang, X. F. “Information Uncertainty and Stock Returns.” Journal of Finance, 61 (2006), 105–137.

