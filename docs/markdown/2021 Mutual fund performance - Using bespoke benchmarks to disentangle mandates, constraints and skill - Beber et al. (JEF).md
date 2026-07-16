# Mutual Fund Performance: Using Bespoke Benchmarks to Disentangle Mandates, Constraints and Skill

Journal of Empirical Finance 60 (2021) 74–93

Contents lists available at ScienceDirect

Journal of Empirical Finance

journal homepage: www.elsevier.com/locate/jempfin

Mutual fund performance: Using bespoke benchmarks to
disentangle mandates, constraints and skill
Alessandro Beber a,1, Michael W. Brandt b,∗,1, Jason Cen c,1, Kenneth A. Kavajecz d,1
a BSYS, BlackRock, United Kingdom of Great Britain and Northern Ireland
b Fuqua School of Business, Duke University, United States of America
c University of Exeter Business School, United Kingdom of Great Britain and Northern Ireland
d Phoenix Rising Advisory, United States of America

A R T I C L E I N F O

## Abstract

JEL classification:
G12
G23

Keywords:
Mutual funds
Performance evaluation
Benchmarks
Mandates and constraints

## 1. Introduction

While no two mutual funds are alike in terms of their mandates and constraints, metrics used
to evaluate fund performance relative to peers typically fail to account for these differences by
relying on generic benchmark indices and rankings. We develop a methodology to construct
a conditional multi-factor benchmark that explicitly incorporates the details of a given fund’s
mandates and constraints. The results suggest that (i) mandates and constraints are economically
important and affect funds differently, (ii) in general, the average mutual fund has a much
improved track record when comparing themselves to a bespoke benchmark, and (iii) the rank
ordering of fund bespoke performance relative peers is significantly different than the original
rank ordering suggesting advisors and board of directors would make better decisions regarding
compensation and performance assessment respectively, if they incorporate the impact of
mandates and constraints.

Consider that as of 2019, actively managed U.S. mutual funds controlled $13.9 trillion in total net assets.2 Accurately measuring
the performance of these funds is important to household investors, who hold the overwhelming majority of those assets as retirement
savings, fund advisors, who must internally evaluate the performance of the fund’s portfolio manager, and fund directors/trustees,
who are required under the Investment Company Act of 1940 to annually review fund performance, among other items, as part of
renewing the contract with the fund advisor. Traditionally, the basis for performance measurement is a comparison of the fund’s
return relative to a chosen benchmark within a defined asset category, e.g. large cap, growth, etc. and then ranked among a set of
peer funds.

A crucial aspect of the appropriateness/accuracy of these performance assessments is the comparability of a benchmark and a
fund’s performance. A mutual fund’s choice of a benchmark traditionally utilizes the same asset investment universe (i.e., domestic
equities, corporate bonds, international equities, etc.), and matches the investment size (large, medium, small, micro, etc.) and style
(i.e., growth, value, momentum, etc.) characteristics. The difference between the fund’s return and the benchmark return is taken
as a measure of performance, or lack thereof. While this measurement process may make sense for index and absolute return funds,

∗ Corresponding author.

E-mail address: mbrandt@duke.edu (M.W. Brandt).

1 We gratefully acknowledge financial support from Inquire Europe. We also thank participants at the FTSE World Investment Forum, Finance Down Under
Conference, EDHEC Business School and Virtual Finance Workshop as well as an anonymous referee and Clemens Sialm for their comments and suggestions. All
remaining errors are our own. All authors contributed equally to the analysis and document.

2 Mutual fund statistics taken from the Investment Company Institute Fact Book: https://www.ici.org/pdf/2018_factbook.pdf.

https://doi.org/10.1016/j.jempfin.2020.12.001
Received 21 October 2019; Received in revised form 8 September 2020; Accepted 2 December 2020
Available online 8 December 2020
0927-5398/© 2020 Elsevier B.V. All rights reserved.

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 1. Large cap equity fund and the market portfolio in a mean–variance framework. The following charts illustrate an example of the standard
comparison between a mutual fund’s performance and its benchmark in a mean–variance framework (Panel A) and the impact of adjusting the minimum-variance
frontier (bespoke benchmarks) for a series of mandates and constraints faced by the mutual fund (Panel B). In Panel B, the mandates and constraints listed are:
A = Fully Invested, B = No Short Sales, C = Concentration Limit, D = Sector Weights match benchmark, E = residual or manager skill.

it ignores fundamental differences between an active mutual fund and benchmark, such as fund mandates and constraints, which are
not imposed on the requisite benchmarks.

As an illustration of the comparability/measurement problem, consider a mutual fund that has a mandate to invest in small
capitalization value stocks, with constraints to be fully invested at all times and have at least 60% of the portfolio companies
be dividend-paying stocks. While a natural benchmark to use would be the Russell 2000 value index, the percentage of dividend
paying stocks within the index is well below 60%. Moreover, because the Russell 2000 value index is static, and not subject to a
fully-invested budget constraint, it does not need to sell a stock in order to buy another stock and vice versa like the active manager
must. As such, differences between a mutual fund and a benchmark may be the results of mandates and constraints, manager skill
or a combination of each. Interestingly, the mandates and constraints that are listed within mutual funds’ prospectuses display
substantial heterogeneity; thus, potentially having differential effects on the performance of funds.3 Said differently, and the central
problem our paper addresses, is that the conventional measure of fund performance is similar to comparing fruit of all varieties:
apples, oranges, strawberries, etc. Thus, it is important academically, practically and regulatorily to find a method to make the
comparison and measurement appropriate and meaningful.

3 Note that if all active funds within the same size/style class were subject to the same mandates and constraints, the benchmark comparison would preserve

the rank ordering of competing funds.

75

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Our analysis develops precisely that methodology to account for the mandates and constraints of a fund manager by adjusting
the relevant benchmark to mirror the fund manager’s mandates and constraints — resulting in an apples-to-apples comparison.
The intuition behind this methodology can be gleaned from taking a simple mean–variance perspective on performance. Consider a
fund of all large capitalization equities over the period 1974–2013, which has a historical return of 13% and a standard deviation of
20%. Panel A of Chart 1 depicts the large capitalization equity fund within a standard minimum variance frontier calculation over
the same period. Because the fund is below the Capital Market Line (CML), it delivers less return, or more risk, than its minimum
variance benchmarks. It is standard to interpret the fund manager as generating negative alpha. It is this interpretation that is
inappropriate, given the substantial differences in mandates and constraints between the fund and the benchmark. Consider now
‘adjusting’ the minimum-variance frontier to account for the fund specific mandates/constraints. Panel B of Chart 1 provides an
illustration of how the frontier may be altered to accommodate the portfolio’s unique set of mandates and constraints. This in turn
alters the interpretation of alpha generation and skill. Thus, the models used as standard benchmarks, while full of intuition about
the trade-off between risk and return, are built upon many strong assumptions. For example, in the Capital Asset Pricing Model
(CAPM), two-fund separation exists in the presence of full information, simple and clear preferences over only risk and return, and
the absence of practical frictions facing the portfolio manager.

Our results show that once benchmarks are properly adjusted, fund mandates and constraints display a wide range of effects on
both the benchmark returns and manager’s portfolio choice problem. Specifically, the investment universe (size and style) constraints
cost funds an average excess risk of 190 basis points, with the small and value styles being the most costly; moreover, cash holdings
and leverage add 177 basis points, limits on short-sales adds 80 basis points, and turnover restrictions contribute 141 basis points
in average added costs.4 In addition, the bespoke fund performance results in an average 30 to 40% reduction in fund manager
underperformance with a corresponding increase in the variance of performance. Not surprisingly, given the heterogeneity in fund
mandates and constraints, the bespoke ranking of peer performance is significantly different than the original ranking, especially for
the highest ranked funds suggesting potentially different investment choices might be made by market participants if armed with
the bespoke peer ranking.

Our analysis has important implications for academics and market participants alike. From an academic perspective, we provide
a flexible methodology to properly compare a fund’s performance to a benchmark. The methodology highlights that while basic
asset pricing models are good at providing intuition regarding risk and return, they are poor at providing an accurate absolute and
relative measurement of the risk/return tradeoff because of their failure to account for the reality of mandates and constraints. In
addition, while all market participants are interested in accurate and meaningful performance measures, our results are particularly
important for those constituencies who take fund mandates and constraints as given, or exogenous, with respect to their objective.
Notable constituencies include (1) mutual fund advisors/management whose objective is to compensate and retain asset managers
that are able to deliver the highest mandate/constraint adjusted performance, i.e. the best performance within the confines of the
fund’s given mandates and constraints, and (2) mutual fund directors/boards whose fiduciary responsibility is to ensure shareholders
are receiving fund performance above and beyond that which can be attributed to the fund’s mandates and constraints. To properly
execute their objectives, both these constituencies require a method to partition a fund’s performance into performance due to the
given mandates and constraints, and performance due to the choices the portfolio manager makes.

The remainder of the paper is organized as follows. Section 2 discusses the related literature. Section 3 describes our methodology.
Section 4 details our sample funds and the mandates and constraints they face. Section 5 provides model estimates and the costs of
individual and joint mandates and constraints on candidate benchmarks. Section 6 concludes.

## 2. Relevant literature

Our work is related to three facets of the financial literature: parametric estimation of asset pricing models, incorporating frictions

in asset pricing models, and mutual funds.

The need for parametric estimation arises because the traditional approaches (mean–variance optimization and factor-mimicking
portfolios) are not feasible and flexible enough to capture fund mandates and constraints. Thus, we adopt the framework of
Brandt et al. (2009) for developing a parametric portfolio in which the vector of portfolio weights is a function of a set of firm
characteristic variables. We extend their original methodology to take account of mandates and constraints, essentially transforming
a high-dimensional constrained portfolio choice problem of individual stocks into a low-dimensional problem expressed through
characteristics.

Researchers have long acknowledged that frictions will deleteriously impact the performance of asset pricing models. However,
the key difference among fund mandates and constraints and other studied frictions is that mandates and constraints are heterogeneous
across funds, while most other frictions have a homogenous impact within the marketplace. One exception, which investigates a
single constraint, is Briere and Szafarz (2017). Their investigation of the impact of short-selling constraints on factor-based portfolios
concludes that accounting for this constraint substantially changes mean–variance performances. The goal of our paper is to account
for the differential impacts of multiple fund constraints and mandates on fund managers and their respective benchmarks. Given few
papers have addressed this issue, we believe our results make an important contribution to the literature.

The literature on mutual funds is vast, whereby a complete review is beyond the scope of this paper; however, there are few areas
that are relevant to our work: rankings, benchmark choice and retail investor behavior. As mentioned earlier, there is considerable

4 The added costs due to these mandates and constraints are average values across all applicable funds in our sample where the target excess return is 8%.

76

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

research which shows the importance and influence that fund rankings have on fund flows and AUM, representative work includes
Blake and Morey (2000) and Del Guercio and Tkac (2008).

A mutual fund’s choice of benchmark is also an important topic. The general consensus from that literature is that the choice of
benchmark has a significant impact on performance, particularly if there is a mismatch between the investment universes. Sensoy
(2009), Mateus et al. (2017), and Cremers et al. (2018) suggest that the benchmark choice may be strategic to bolster performance
relative to peers. Finally, our analysis is related to the behavior of investors in mutual funds. Work by Palmiter (2016) and Friesen
and Nguyen (2018) suggest that retail investors are less than savvy about their investment choices given they appear ignorant of
fund characteristics and unresponsive to risks and fees. Given this characterization of retail investors, it is not difficult to argue that
they would also be unaware of funds mandates and constraints.

## 3. Methodology

This section presents a constrained parametric approach to the traditional mean–variance portfolio choice problem and provides

a description of the data, including information on fund mandates and constraints, which will be used to estimate the model.

### 3.1. Parametric benchmark portfolio policy

There are numerous ways in which benchmarks are calculated in finance. However, creating the proper benchmark to account
for the differences across fund strategies (mandates, constraints) requires a parsimonious and feasible procedure for calculation.
While mean–variance portfolio optimization may be the first method to spring to mind, it can be quickly dismissed as infeasible,
and in addition, it is well known to be subject to unrealistic portfolio holdings. Similarly, factor-mimicking portfolios are not a
suitable alternative, as it does not provide enough flexibility to capture the differences underlying various mandates and constraints.
Consequently, we utilize a parametric portfolio approach as in Brandt et al. (2009), which provides both a feasible and flexible
method for calculating bespoke benchmarks. The intuition behind this approach is similar in spirit to a change in mathematical
basis, whereby the variation and impact of the various constraints and mandates are projected upon fund characteristics rather than
onto a set of portfolio holdings.

Another interpretation of our approach, and one that we will carry through the remainder of the paper, is that any portfolio
that a manager may choose can be decomposed into a set of beta strategies (long-only portfolios) and a set of alpha strategies
(zero-cost hedged portfolios). The exposures to these strategies are the decision variables in the constrained parametric portfolio
choice problem. In contrast to the traditional mean–variance portfolio choice approach, which models nonlinear constraints of the
high-dimensional space of portfolio weights on individual assets, our constrained parametric portfolio choice framework specifies
fund mandates and constraints as linear restrictions on a low-dimensional parameter space and the resulting constrained portfolio
choice problem can be easily solved using quadratic programming.

### 3.2. Econometric model

We begin with a description of our baseline model, the parametric portfolio approach formulated in Brandt et al. (2009), and

then describe the adaptations which allow our analysis of mandates and constraints.

Consider an investment universe of 𝑁𝑡 stocks, whereby any portfolio is parameterized by active portfolio deviations from the
market or benchmark portfolio at time t for stock i as a function of the firm’s observable characteristics, 𝐶𝑡,𝑖. The model starts with
a single-period expected utility maximization over portfolio weights 𝑤𝑡,𝑖 ∶

( 𝑁𝑡∑

[
𝑢

𝑖=1

)]

𝑤𝑡,𝑖𝑟𝑡+1,𝑖

E𝑡

max
{𝑤𝑡,𝑖}𝑁𝑡
𝑖=1

(1)

where 𝑟𝑡+1,𝑖 is the gross (one plus) return on stock i from t to t +1 and the weights 𝑤𝑡,𝑖 sum to one across stocks. In order to
reduce the dimensionality of this maximization, Brandt et al. (2009) propose parameterizing the portfolio weights as a function of
firm characteristics and a low-dimensional set of parameters 𝜃, or 𝑤𝑡,𝑖 = 𝑓 (𝐶𝑡,𝑖; 𝜃)
, in particular, they work with a simple linear
parameterization:

𝑤𝑡,𝑖 = 𝑤𝑡,𝑖 +

1
𝑁𝑡

𝜃⊤ ̃𝐶𝑡,𝑖

(2)

where 𝑤𝑡,𝑖 are the weights of stock i in the market or benchmark portfolio and ̃𝐶𝑡,𝑖 are firm characteristics that are now standardized
(mean zero, standard deviation one) across stocks at each time t. The intuition of this parameterization is that the optimal portfolio
weights are deviations from benchmark weights that depend only on the firms’ standardized characteristics. The standardization
ensures that the benchmark tilts sum to zero so that the sum of the portfolio weights equals the sum of the benchmark weights,
which in turn, equals one. Finally, the authors argue that the 1∕𝑁𝑡 normalization is required to keep the magnitude of tilts stable
as the cross-section of stocks grows over time.

With this simple linear parameterization, the high dimensional optimization in Eq. (1) can be rewritten as much lower
dimensional one with respect to the parameters 𝜃. Moreover, since these parameters are time invariant by assumption, the
conditional expectation can be conditioned down to an unconditional one using the law of iterated expectations, resulting in:

( 𝑁𝑡∑

(

[
𝑢

𝑖=1

max
𝜃

E

𝑤𝑡,𝑖 +

1
𝑁𝑡

𝜃⊤ ̃𝐶𝑡,𝑖

)]

)

𝑟𝑡+1,𝑖

77

(3)

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Finally, Brandt et al. (2009) operationalize this parametric portfolio optimization problem by estimating the unconditional

expectation with a sample average:

max
𝜃

1
𝑇

𝑇
∑

𝑡=1

( 𝑁𝑡∑

[
𝑢

𝑖=1

(

𝑤𝑡,𝑖 +

1
𝑁𝑡

𝜃⊤ ̃𝐶𝑡,𝑖

)]

)

𝑟𝑡+1,𝑖

(4)

Intuitively, the optimal parametric tilts from the benchmark portfolio maximize the realized utility of the portfolio in-sample.

Using the Brandt et al. (2009) approach, we adapt the model in three important ways to accommodate our investigation of
mandates and constraints. For the first departure, we assign each stock to an industry, a size group, and a style group. Specifically,
we consider in our application 𝐼 = 10 industries based on top level SIC codes, small and large size groups based on the median firm
capitalization, and value and growth style groups based on the median book-to-market ratio (i.e., 𝑆 = 4 size and style groups). In
the context of the parametric portfolio policy, we then associate each stock separately with (1) the average characteristics of the
industry, size, and style group to which the firm belongs, and (2) the deviation of the firm’s characteristics from these industry, size,
and style group averages. This modeling choice allows the parametric portfolio to independently tilt into industry, size and style
groups for broad group investments as well as into individual firms within each industry, size and style group for group-neutral
stock investments. We refer to the average characteristics of the industry, size and style groups as across group characteristics and
the firm specific deviations as within group characteristics.

As in Brandt et al. (2009), both sets of characteristics are cross-sectionally normalized to ensure that portfolio tilts from the
market or benchmark portfolio add up to zero and are not affected by changes in the universe composition such as doubling
the number of firms by simply splitting them up. Specifically, the across group characteristics are demeaned so that group tilts
can be market or benchmark neutral and are scaled by the relative market capitalization of each firm versus the whole group to
ensure that group tilts are market capitalization weighted. Intuitively, as the portfolio tilts from one group to another, it does so
proportionally more for larger firms within the groups. The within group characteristics are, in addition to already being demeaned
by construction, normalized by the relative market capitalization of the group versus the whole market. This normalization scales
the active investment within each group by the market capitalization of the group instead of the number of firms within the group.
The second departure from Brandt et al. (2009) is that we split both the across and within group characteristics into positive and
negative values with separate coefficients on each. This allows the portfolio to more aggressively overweight firms with positive
characteristics than underweight firms with equally negative characteristics, or vice versa. However, by breaking the link between
over and under-weights relative to the market or benchmark portfolio, the active tilts may no longer sum to zero or be self-funded.
To compensate, we introduce another coefficient on the market or benchmark portfolio so that if the active tilts are net positive
(negative) the allocation to the market or benchmark portfolio is adjusted appropriately less (more) than 100 percent so that the
sum of portfolio weights still add up to one. This is the final modeling departure from Brandt et al. (2009).

To summarize, the optimal portfolio weight at time t for stock i, denoted 𝜔𝑡,𝑖, is parameterized as follows:

𝜔𝑡,𝑖 = 𝛽0𝜔𝑡,𝑖 + 𝛽𝑐+

𝑡,𝑖 + 𝛽𝑐+

𝑡,𝑖 + 𝛼𝑐𝑡,𝑖 + 𝛼𝑐𝑡,𝑖

(5)

where 𝜔𝑡,𝑖 is the weight of the market or benchmark portfolio at time t for stock i, 𝑐𝑡,𝑖 is a vector of normalized and scaled average
characteristics for the industry, size, and style group to which stock i belongs at time t (the across group characteristics), 𝑐𝑡,𝑖 is a vector
of differences between the firm’s characteristics and the firm’s industry, size, and style group average characteristics (the within group
characteristics). 𝑐+
𝑡,𝑖 are vectors that contain the positive values of across and within group characteristics, respectively, and
zeros when the corresponding characteristics are negative.

𝑡,𝑖 and 𝑐+

[𝛽0, 𝛽, 𝛽, 𝛼, 𝛼] are the parameters governing the optimal portfolio weights. [𝛼, 𝛼] tilt the portfolio weight symmetrically away
from the market or benchmark weight based on the across and within group characteristics of the firm. These are the zero-cost
alpha strategies discussed in the previous section. [𝛽, 𝛽] allow this tilt to be asymmetric, where positive (negative) values create a
tilt that overweighs firms with positive (negative) characteristics more than it underweights firms with equally negative (positive)
characteristics. Finally, 𝛽0 scales the benchmark weight to allow for tilts that do not sum to zero in the cross-section, or are not
self-funded. The three terms associated with the beta coefficients represent the long-only beta strategies. To reduce the number of
free parameters, we assume that the loadings on the within across and within group characteristics are the same for all 10 industries.
With K characteristics, this assumption reduces the number of coefficients to 1+16K.5

An alternative interpretation of our parameterization is the common practice of funds attributing performance relative to the
benchmark to ‘‘allocation’’ (across groups) and ‘‘selection’’ (within groups). ‘‘Selection’’ is that portion of the fund’s return that is due
to selecting outperforming stocks within a sector, while ‘‘allocation’’ is that portion of the return due to being in outperforming
sectors, independent of which stocks were in the fund’s portfolio. In our parameterization, selection skill comes from non-zero 𝛼
and 𝛽 loadings while allocation skill is due to non-zero 𝛼 and 𝛽 loadings. In addition, it is common practice for a mutual fund to
impose minimum and maximum allowable deviations from the benchmark weights in the requisite benchmark portfolio, sometimes
called sector/industry bands. These limits would be corresponding upper constraints on the parametric portfolio parameters.

5 Each of the four size and style groups has two coefficients on K across industry characteristics and two coefficients on K within industry, size and style

group characteristics.

78

A. Beber, M.W. Brandt, J. Cen et al.

### 3.3. Investment universe

Journal of Empirical Finance 60 (2021) 74–93

We measure the impact of various mandates and constraints relative to the unconditional minimum variance frontier. Thus, we
must define the unconditional investment universe as well as the size and the style groups. The investment universe includes all
traded stocks, except those whose price is below $5 per share, as well as stocks whose market capitalization is below the 20th
percentile in the cross-section. These exclusions are meant to minimize the effect of extreme observations due to infrequent trading
of illiquid securities on our results. We define the size and style groups based on market capitalization and the book-to-market ratio
using NYSE breakpoints. A stock with a market equity below the 20th percentile is classified as ‘‘micro-cap’’ (thereby excluded as
explained above), between the 20th and 50th percentile (median) as ‘‘small cap’’, and above the 50th percentile (median) as ‘‘large
cap’’. Similarly, a firm with a book-to-market ratio above the 50th percentile (median) is classified as ‘‘value’’ and correspondingly
below as ‘‘growth’’. Finally, we impose consistency between the investment universe and the size and style groups in two ways.
First, we set the loadings associated with size and style groups outside the investment universe to zero. Second, we renormalize the
market capitalization weights of all firms in the universe within each size and style group.

### 3.4. Mandates and constraints

There are numerous mandates and constraints that obfuscate the measurement of fund performance relative to a benchmark; thus,
a comprehensive investigation of each one is infeasible. Moreover, fund mandates and constraints display incredible heterogeneity
with respect to how widely they are communicated, the ease/difficulty with which they can be incorporated into our parametric
portfolio problem, and whether they are self-imposed or part of market-wide financial regulation. The mandates and constraints
we focus on in this paper are set out in the fund prospectus or Statement of Additional Information (SAI), are typically chosen by
the fund, and are widely communicated to investors (see Section 4 below for a detailed description of our data). Specifically, we
incorporate five mandates/constraints into our parametric benchmark models: investment universe, short-sales, borrowing/lending,
portfolio turnover and transaction costs, as these are widely communicated to investors, parsimoniously modeled, and easily
interpretable.

#### 3.4.1. Investment universe

It is relatively common for a mutual fund to have a restricted or targeted investment universe such as growth versus value
or large versus medium versus small capitalization firms. Universe restrictions are simple to impose in our framework by simply
redefining and renormalizing the investment universe in Section 3.3.

#### 3.4.2. Short sales

(𝛼, 𝛼) 𝚤2𝐾𝑆

Some mutual funds are allowed to short-sell to a limited extent. Many funds are prohibited from short-selling all together.
Suppose a fund is allowed to hold a total short position up to q ≥ 0, then a sufficient condition for this constraint to be satisfied
≤ 𝑞 since the long–short alpha strategies have a short position by design while the beta strategies are long-only by
is
construction. Note that this parameter constraint is sufficient and likely overly restrictive, since some additional allocation to the
alpha strategies can be offset by the long holdings of the beta strategies without producing a total net short position that exceeds
the limit.

#### 3.4.3. Borrowing/lending

Cash borrowing and lending constraints essentially place an upper (𝜋) and lower (𝜋) bound on the riskless asset, where 𝜋 ∈
{0, 1] is the cash holding limit and 𝜋 ≤ 0 is the borrowing limit. Translating these constraints to parameter restrictions obtains:
(
𝛽0, 𝛽, 𝛽

𝚤2𝐾𝑆+1 ∈ [1 − 𝜋, 1 − 𝜋] since only the long-only strategies are impacted by borrowing and lending.

)

#### 3.4.4. Portfolio turnover

A constraint on the extent of trading, or turnover, within the portfolio is modeled by requiring (monthly) turnover 𝑇 𝑂 (𝑤) =
to be bounded above by 𝑢. Given all strategies are impacted by a constraint on trade, the turnover constraint amounts
𝛥𝑤𝑡,𝑖|
𝑖=1 |
|
|

𝑬 ∑𝑁
to the following sufficient condition in terms of the parameters of the portfolio policy rule:
+ 𝛼𝑇 𝑂 (𝑐)

+ 𝛽𝑇 𝑂 (𝑐+)

+ 𝛽𝑇 𝑂 (𝑐+)

+ 𝛼𝑇 𝑂 (𝑐) ≤ 𝑢

𝛽0𝑇 𝑂 (𝑤)

#### 3.4.5. Transaction costs

Finally, we model transaction costs by adding a function of trades to the objective function of portfolio return variance:

𝑇 𝐶 =

1
2

𝜂𝛥𝑤′

𝑡𝛴𝑡𝛥𝑤𝑡

where 𝜂 is a constant which governs the level of trading costs. We calibrate the median level of this parameter using the following
mean–variance criterion:

𝐸 [𝑤𝑡𝑅𝑡+1 − 𝑅𝑓 ,𝑡

]

−

𝐴
2

[𝐸 (𝑤𝑡𝑅𝑡+1

)2

+ 𝜂𝐸 (𝛥𝑤𝑡𝑅𝑡+1

)2

] = 0

(8)

This function sets equal the utility of holding a value-weighted market index, which is rebalanced each month, with the utility of
holding cash, given the intensity of transaction cost 𝜂. Given standard assumptions, we obtain a medium transaction cost intensity

79

(6)

(7)

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

of 𝜂 = 50.6 We also consider two additional liquidity environments, one that is more liquid, where 𝜂𝑙𝑜𝑤 = 1
𝜂 = 25, and another that
2
is more illiquid where 𝜂ℎ𝑖𝑔ℎ = 2𝜂 = 100. The latter liquidity environment could be interpreted as either fragmented markets, markets
with few liquidity providers, or perhaps periods of market downturns as in 1987, 1997 and 2008.

### 3.5. Constrained parametric portfolio choice problem

Combining the basic parametric portfolio problem with the parameterized mandates and constraints yields the following problem

presented here in matrix notation:

( 1
2

min
𝜃

)

𝜃′𝛺𝜂𝜃

where 𝛺𝜂 = 𝐸

[
𝑋′

𝑡 𝑅𝑒

𝑡+1𝑅𝑒′

𝑡+1𝑋𝑡

]

+ 𝜂𝐸[𝛥𝑋′

𝑡 𝑅𝑒

𝑡+1𝑅𝑒′

𝑡+1𝛥𝑋𝑡]

(9)

subject to the following constraints:
]

[

𝑡 𝑅𝑒

𝑡+1

= 𝜇𝑒

1 − 𝜋, 1 − 𝜋]
≤ 𝑢
𝛥𝑋′
𝑡 |
|

𝚤𝑁

𝑋′
≤ 𝑞
[

𝜃′𝐄
𝜃′𝒆𝛼
𝜃′𝒆𝛽 ∈
𝜃′𝐄 |
|
𝜃 ≥ 0

∶ mean return target

∶ short sale
∶ borrowing and lending
∶ turnover
∶ fund level long only

The vectors included in the above problem can be interpreted as follows. The vector 𝒆𝛽 selects only those coefficients that correspond
to the long-only strategy, i.e. 𝛽0, 𝛽, 𝑎𝑛𝑑 𝛽; therefore, they are present in the mean return target and borrowing/lending constraint.
Correspondingly, the vector 𝒆𝛼 selects those coefficients that pertain to the hedged portfolios, i.e. 𝛼 𝑎𝑛𝑑 𝛼; thereby only included
in the short-sale constraint. Note that any universe constraints are implicit in the initial dataset construction, and that we added a
fund level constraint on the parameters which should be non-binding provided firm characteristics are signed appropriately.

## 4. Data

### 4.1. Market data

To empirically estimate the parametric model, we require equity returns and accounting data as well as information regarding

mutual fund mandates and constraints. We describe each in turn.

We obtain monthly return, price per share, and shares outstanding of individual U.S. companies traded in the NYSE, AMEX,
and NASDAQ from the Center for Research on Security Prices (CRSP). We then collect corresponding accounting variables as well
as Standard Industry Classification (SIC) codes from the CRSP-Compustat merged data set. In the case of a missing SIC code, we
complement it using data from CRSP. Stocks are then categorized into 10 industry sectors based on the definitions outlined on
Kenneth French’s Data Library. The sample period is January 1974 to December 2013.

For each firm, we construct three conditioning characteristic variables: size, or market equity; value, or book-to-market ratio;
and return momentum. Specifically, market equity is defined as the log of the common share price times the number of common
stock shares outstanding at the end of each June. Book-to-market is measured as the log of the ratio of book equity measured at
the most recent fiscal year-end within the prior calendar year to the market equity measured at the end of the prior calendar year
(December). Finally, momentum is defined as the one-year return lagged by one month to remove any short-term reversal effects.7

### 4.2. Fund mandates and constraints

The set of mutual funds we consider are all U.S. equity capital appreciation funds. Our mutual fund sample choice is based on a
singular, clear objective (capital appreciation) as well as a parsimonious sample of 141 funds, making it feasible to collect the data.
For our main analysis we further narrow the sample to the 71 mutual funds with at least a 10-year track record. In order to gather
the mandate and constraint data for our funds, we reviewed the prospectus for each one of our sample (capital appreciation) funds.
Specifically, we reviewed and hand collected data from the 485A and 485B Prospectus of Security (POS) as well as the Statement
of Additional Information (SAI) that were submitted to the SEC within, or closest to, the fourth quarter of 2009.8 In reviewing these
prospectuses, we recorded data on 4 dimensions: security holdings, investment level, other securities, and benchmarks. See Table 1
for a specific list of variables coded.

The security holding describes the universe of securities that the fund is constrained to invest within. Common specifications
include growth versus value, large, medium and small capitalization equities, and foreign holdings, which for most funds were
relatively easy to identify. Investment level refers to the extent that the fund is able to buffer fund flows (in or out) with borrowing
or the ability to hold cash (not be fully invested). The language surrounding the investment level tends to be broad in order to
accommodate infrequent/rare occurrences. For example, many funds state they have the ability to borrow and hold cash on a

6 In solving for 𝜂, we assume that relative risk aversion is 𝐴 = 5, the equity risk premium is 8%/12 = 0.0067, the variance of the market return is
16%2)
(
7 For a further description of the industry sectors and market variables see Kenneth French’s Data Library website: http://mba.tuck.dartmouth.edu/pages/

∕12 = 0.0021, the mean squared variance-adjusted turnover of the value-weighted market index is 1.2 × 10−5.

faculty/ken.french/data_library.html.

8 See http://www.sec.gov/edgar/searchedgar/prospectus.htnm.

80

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 1
Mutual Fund Mandates and Constraints. We select as our sample the set of Capital Appreciation mutual funds.
In searching the CRSP mutual fund database, we identified 141 Capital Appreciation Mutual Funds as of June
2009, which we take as our sample. For each fund, we employ the following procedure to collect information on
the securities, methods, and constraints they face. As each mutual fund is required to provide the Securities and
Exchange Commission (SEC) with a prospectus (485POS) and an annual/semiannual report on holdings (N-30D),
we review these two documents filed closest to the last quarter of 2009, and code the following information:

Security Holdings:
Names:
Type:
Style:
Size:
Industry:
Foreign:

Investment Level:

Max # of securities, (U) Unconstrained
Equity (E), Fixed Income (FI), or Both (B)
Growth (G), Value (V)
Large (L;%), Medium (M;%), Small (S;%)
Unconstrained (U), List
Max %

Ability to Borrow:
Ability to Hold Cash:
Turnover:

(Yes/No)
(Yes/No)
(% Given)

‘‘Constrained buys’’
‘‘Constrained sells’’
‘‘Constrained trade’’

(N-30D file)

Other Securities:

Securities Lending:
Shorting:
Derivatives:

Benchmark:

(Yes;%, No)
(Yes;%; No)
(Yes;%, No)

None Referenced (NR), Specific Index (List)

Volatility:

Unconstrained (U), Managed (M), % or Index identified

Table 2
Summary Statistics on Sample Mutual Fund Mandates and Constraints. We select as our sample the set of Capital Appreciation mutual funds. In searching
the CRSP mutual fund database, we identified 141 Capital Appreciation Mutual Funds as of June 2009. For our main analysis, we further select 71 out of
the 141 identified funds with more than 10 years of track record, which we take as our sample. For each fund, we employ the following procedure to collect
information on the securities, methods and constraints they face. As each mutual fund is required to provide the Securities and Exchange Commission (SEC)
with a prospectus (485POS) and an annual/semiannual report on holdings (N-30D), we review these two documents filed closest to, the last quarter of 2009.
This table reports the average of key fund characteristics and constraints for both the whole sample (Row ‘‘All’’) and subsamples of funds with a focus on a
certain size (large vs small) or style (growth vs value) groups. The last row shows the numerical values we choose to represent the unconstrained cases. For
example, if the cash holdings of a fund without cash limit is capped by 1, or 100%.

Sample Funds

AUM million $

\# of Names

Large
Small
Growth
Value
All
Unconstrained

1055.76
541.17
1378.86
1637.41
1147.49

16
12
27
11
71

Constraints

Leverage

1.42
1.70
1.59
1.65
1.48
2.00

Cash

0.54
0.70
0.53
0.48
0.59
1.00

Short-sale

Turnover

1.54
1.58
1.34
1.65
1.46
2.00

0.44
0.56
0.79
0.54
0.73
2.00

‘‘temporary and defensive basis’’, and yet do so only on rare occasions. Other securities captures the extent to which the fund is able
to use derivative contracts as well as taking a short position in securities and lending securities to other counterparties. Benchmarks
are a key piece of information for our study as it defines the metric by which the fund has chosen to measure its own performance.
Most funds specify a broad index that is representative of the security holding universe that the fund is constrained to invest within.
Recall the role of a prospectus is to provide investors accurate information about the investment strategy, risks, past performance,
operations, restrictions, fees and management, so investors are able to make an informed decision about whether to invest. Not
surprisingly, the ordering of topics, form of presentation and even the language used within these prospectuses often follows a
common template.9 Heuristically, we understand that the generalizations/legal language within the prospectuses does not always
match practice. Moreover, we acknowledge that some of these mandates and constraints are explicit while others implied. For
example, while a majority of funds have the ability to mitigate fund inflows/outflows, in practice they maintain a low cash position
and borrow little, thereby investing when they receive inflows and selling when they are redeemed to remain fully invested.

After gathering and reviewing the prospectus mandate and constraint data, we take as the most relevant constraints to analyze:
(1) mandates on the investment universe, (2) borrowing/lending constraints, (3) short-sale constraints, (4) turnover constraints, and
(5) transaction costs.

9 For

example,

see

the

following links

for

representative prospectuses within our

sample. http://www.sec.gov/Archives/edgar/data/100334/

000010033410000014/pea125-2010.htm http://www.sec.gov/Archives/edgar/data/275309/000072921809000035/main.htm.

81

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 2 presents some summary statistics on the mandates/constraints facing our sample funds. The sample has a good mix of
funds within each of the size/style groups, with large/growth having the largest number of funds and small/value having the smallest
number. Note that some mandates/constraints are rather uniform, for example, cash and short-sale, while others, like leverage and
turnover, have more variation.

## 5. Properties of constrained minimum variance frontiers

We perform two estimations of the constrained minimum variance frontiers, one in-sample and the other out-of-sample; each
meant to address a different research question. The in-sample estimation suits our purpose of ex-post evaluation of fund performance
relative to an appropriately constrained benchmark, while the out-of-sample estimation provides a realistic estimation of the
constrained portfolio using rolling historical data. The out-of-sample estimation establishes a natural robustness check of the in-
sample results with respect to overfitting the parameters and also provides a window into how real-time, rolling estimation may
impact the mandate and constraint costs.

### 5.1. In-sample portfolio construction

We present the in-sample results in three complimentary ways. First, we present figures that show the impact of incorporating
individual mandates and constraints on the minimum variance frontier. Second, we detail the changes to portfolio weights when
incorporating mandates and constraints, and finally, we investigate the impact that mandates and constraints have on particular
investment and trading strategies. In what follows we discuss each in turn.

We begin by addressing the following question: what would be the return variance of a portfolio constrained to have (i) the same
mandates and constraints and, (ii) the same average return as the fund in consideration? To this end, we estimate the parameters
of the constrained portfolio, theta, for any given value of mean excess return using the full-sample of data/information. We then
construct the constrained portfolio based on the point estimates of parameters, ̂𝜃𝐼𝑁 .

Charts 2–5 display the effects of the various mandates and constraints on the minimum variance frontier. Intuitively, the
constrained minimum variance frontiers tend to be located inside (less return and more risk) the unconstrained or less constrained
frontiers. The following analysis addresses each mandate/constraint individually.

Chart 2 displays the effects of constraining borrowing and lending. On one hand, we find that the borrowing constraint reduces
the efficiency only marginally because beyond the tangent portfolio, the Sharpe Ratio of the benchmark without cash diminishes very
slowly, which leaves little room for leverage to have a demonstrable difference (Panel A). On the other hand, limiting cash holdings
can decrease the efficiency of the frontier substantially (Panel B). To provide some perspective on these effects, an unconstrained
fund manager would be able to achieve an annualized average return of 8% in excess of the time-value of money at the cost of a
relatively low level of risk, an annualized standard deviation of 6%. The counterpoint to that example is a fund manager who is
allowed to hold no more than 20% of their portfolio in cash; they would have to induce a standard deviation of 10% to achieve the
same level of return. Moreover, in the event that the fund was fully invested, the fund manager would generate a standard deviation
of 13% for the same level of return.

Similarly, we examine the effects of the remaining mandates and constraints on the minimum variance frontier; however, we
exclude the risk-free asset from the investment opportunity set to more clearly understand the links between the remaining mandates,
constraints, and asset allocation decisions. Chart 3 displays the results for the constraint to refrain from short-selling. Interestingly,
short-sale constraints appear to impact only the upper envelope (efficient portion) of the minimum variance frontier. As an example,
for a relatively low return target, the imposition of short-sale constraints does not force a substantial increase in the standard
deviation. Thus, our results suggest that the usefulness of being able to short-sell a stock only has an impact when it is being used
as a financing vehicle for the purchase of a high return (high variance) asset.

Chart 4 displays the results of mandates related to the investment universe. Panel A displays the results for large versus small
stocks and Panel B displays the results for growth versus value styles. The results in Panel A display an interesting contrast between
low and high return targets. Notice that the two constrained frontiers intersect, whereby the frontier for large-cap stocks dominates
that of small caps for returns below 13% and vice versa for the region above 13%. This suggests that during economic downturns,
which are often accompanied by a ‘‘risk-off’’ environment, small-cap funds will face more headwinds than large-cap funds for
the same level of target return. Perhaps not surprisingly, Panel B shows that limiting a manager’s investment universe imposes
a cost whether the style is growth or value. However, value managers face a higher implied cost than do growth managers and the
discrepancy increases with the level of the target return. The results suggest that value managers need to rely on high risk — high
reward stocks, only a few of which generate the targeted return.

The results on asset trading constraints are presented in Chart 5. Panel A displays the bespoke minimum variance frontiers for
various levels of transaction costs. In the context of our model, the reader should think of transaction costs broadly, including but not
limited to: liquidity costs (bid–ask spreads, depth considerations, price impact), commissions or soft dollars, 12(b)-1 fees, back-office
costs, e.g. TA fees. As intuition would serve, the results show that increasing levels of transaction costs impose less efficient frontiers
in the way of parallel shifts in the frontier over the upper envelope (efficient) portion of the frontier. This suggests that funds that
have poor trading capabilities, lack an in-house distribution system, or trade within inherently illiquid markets are at a disadvantage
to funds not facing those same constraints. Panel B displays the results imposing various levels of turnover constraints. Intuitively,
the tighter the restriction on turnover, the less trading is allowed to manage flows in and out of positions, and the lower the expected
return where the turnover constraint is binding. Thus, funds with high expected return targets with constraints on turnover feel the
impact of this constraint the most.

82

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 2. Impact of borrowing and lending constraints on the minimum variance frontier. The following charts illustrate the impact of imposing constraints
on borrowing (Panel A) and cash holdings (Panel B) on the minimum-variance frontier with, and without, the presence of a riskless asset.

Chart 3. Impact of short-sale constraints on the minimum variance frontier. The following charts illustrate the impact of imposing constraints on short-sales
on the minimum-variance frontier without the presence of a riskless asset.

As a complement to the impact of mandates and constraints on the minimum variance frontier, Table 3 presents the impact that
these same mandates and constraints have on the portfolio weights. Panels A, B and C present results for a mean excess return of 4,
8, and 16%, respectively. A comparison of the various bespoke frontiers relative to the unconditional minimum-variance frontiers

83

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 4. Impact of investment universe constraints on the minimum variance frontier. The following charts illustrate the impact of imposing constraints
on the universe of stocks from which the fund can choose on the minimum-variance frontier without the presence of a riskless asset. Panel A addresses size
— Large versus Small, while Panel B address style — Growth versus Value.

shows that mandates and constraints, other than the investment universe: (1) are less concentrated, as seen by smaller maximum
and minimum weights, (2) have fewer short positions, and (3) have lower turnover. There are however, notable exceptions to the
above generalization that are worth broaching. First, sector-neutral portfolios targeting higher excess returns (Panel C) require more
concentrated weights, more short-selling and more intensive turnover than the unconstrained case, as all funds strain to reach a
high expected excess return with their portfolio choices. Second, constraining the investment universe on size or style leads to
more extreme tilts to active trading strategies in order to maintain a given expected excess return in their constrained investment
universe. This is particularly true for small stock and value funds. Lastly, as expected, the imposition of transaction costs induces
lower turnover as managers seek to avoid trading costs. However, transaction costs also have an odd effect in that for high targeted
returns, portfolio managers resort to more extreme bets through concentrated portfolios and larger short positions. We suspect the
pressure of a high return target induces managers to employ a buy-hold strategy where large positive bets are funded with large
short positions.

Finally, we provide insights into how the imposition of mandates and constraints on the model impact traditional trading
strategies. Intuitively, we investigate how a fund manager would reallocate among various trading strategies when faced with
mandates and constraints. For brevity, we focus our attention on the impact of mandates and constraints within the environment
of an 8% excess market premium. Table 4 displays our results. Panel A focuses on sector allocation (across group), while Panel
B highlights stock selection (within group). Within each panel, changes to loadings on size, book-to-market and momentum are
reported for size-style combinations. For the sector allocation strategies (Panel A), the value-small universes are unaffected by the
constraints, while growth (large and small) and value-large are affected through loadings on style (book-to-market). The impact
is particularly pronounced for constraints on short-sales and turnover and imposed transaction costs. Turning to Panel B, stock
selection strategies, the growth style is unaffected by the imposed constraints; however, value-(large and small) are slightly altered
through size (market capitalization), particularly in the presence of transaction costs.

84

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 5. Impact of transaction cost constraints on the minimum variance frontier. The following charts illustrate the impact of various levels of transaction
costs (Panel A) and turnover (Panel B) on the minimum-variance frontier without the presence of a riskless asset. For transaction costs, low, medium and high
are defined as: 1
2

normal costs, normal costs, and double costs, where normal is calibrated in a mean–variance framework.

### 5.2. Out-of-sample portfolio construction

Our out-of-sample analysis begins by using data from January 1964 through December 1973 to estimate the coefficients of the
initial portfolio policy. Using those initial parameter estimates, we form the out-of-sample portfolio for the next month, January
1974. Then, in recursive fashion we expand the sample by one month, rebalancing the portfolio using the new parameter estimates
month-by-month. Finally, using the entire sequence of out-of-sample portfolio estimates, we recalculate the relative performance of
our sample capital appreciation funds against their respective bespoke benchmarks, over a 3, 5, and 10-year horizon as is feasible
given the tenure of our sample funds.

As a robustness check, we analyze the correlation of returns between the in- and out-of-sample benchmark portfolios without
cash for a spread of excess return targets. The out-of-sample portfolios are highly correlated with the in-sample portfolios, where
the correlation for 4% excess return is 0.97 and drops monotonically to 0.93 at an excess return of 32%. Therefore, we are confident
in both the model specifications and the ability to utilize a rolling portfolio rebalancing to investigate the impact of mandates and
constraints. In addition, Chart 6 compares the performance of the in-sample and out-of-sample benchmarks on standard deviation
of returns, average excess return, and the Sharpe ratio in Panels A, B and C, respectively. The standard deviation estimates are very
similar, suggesting an even spread of return variation over time where the in-sample estimates provide lower standard deviations
below 25%. In contrast, the average excess return between the two sets of estimates diverges sharply above the inflection point of
12%, with the in-sample estimates, perhaps not surprisingly, providing higher average excess returns. Finally, combining these two
sets of results, we learn from the Sharpe Ratio results in Panel C that the two sets of estimates are similar for reasonable excess return
targets, but diverge above a target of 20% where the out-of-sample portfolio deliver a maximum Sharpe ratio of 1.0 compared to 1.2
for the in-sample portfolio. Thus, in general, the relatively small difference between the performance of the two sets of portfolios
over reasonable excess return targets lends strong support to our model and its specification.

85

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 3
Portfolio Weights for the In-Sample Constrained Parametric Model. This table presents summary statistics regarding the constrained parametric portfolio
weights given the target mean excess return of 4% p.a. (Panel A), 8% p.a. (Panel B), and 16% p.a. (Panel C). For each panel, we report the time-series averages
of the mean absolute value of portfolio weights (weight, abs.val., %), the maximal weight (max weight, %), the minimal weight (min weight, %), the total weight
of the short positions (short weights), the fraction of stocks being shorted (short fraction), and turnover, measured as absolute value of changes in portfolio
weights summed across all stocks.

Panel A: Mean Excess Return of 4%

Uncon

Sector neutral

Short sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

0

Growth

Value

Small

Large

Low

Med

High

<0.2

<0.5

<1

Weight, abs.val.(%)
Max weight (%)
Min weight (%)
Short weights
Short fraction
Turnover

0.16
9.54
−1.11
−0.64
0.26
0.37

0.13
9.12
−1.02
−0.43
0.30
0.30

0.07
8.40
0.00
0.00
0.00
0.18

0.20
8.45
−1.44
−0.37
0.20
0.23

0.22
13.82
−0.24
−0.12
0.28
0.18

0.18
14.67
−0.52
−0.12
0.35
0.21

0.21
9.55
−1.03
−0.28
0.31
0.28

0.11
5.70
−0.53
−0.29
0.25
0.20

0.10
4.63
−0.37
−0.21
0.24
0.16

0.09
3.93
−0.21
−0.11
0.21
0.12

0.10
7.71
−0.89
−0.23
0.10
0.18

0.16
9.54
−1.11
−0.64
0.26
0.37

0.16
9.54
−1.11
−0.64
0.26
0.37

Panel B: Mean Excess Return of 8% (Current market premium)

Uncon

Short sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

0

Growth

Value

Small

Large

Low

Med

High

<0.2

<0.5

<1

Weight, abs.val.(%)
Max weight (%)
Min weight (%)
Short weights
Short fraction
Turnover

0.22
8.25
−1.65
−0.75
0.32
0.41

0.16
7.91
−1.48
−0.41
0.31
0.32

0.08
7.51
0.00
0.00
0.00
0.19

0.28
7.09
−1.99
−0.48
0.25
0.28

0.37
10.34
−1.08
−0.34
0.32
0.33

0.26
12.57
−1.01
−0.18
0.35
0.22

0.27
8.40
−1.70
−0.36
0.29
0.33

0.16
4.86
−1.00
−0.44
0.27
0.25

0.14
4.14
−0.68
−0.28
0.24
0.19

0.11
3.60
−0.37
−0.12
0.20
0.13

0.13
6.63
−1.11
−0.25
0.13
0.18

0.22
8.25
−1.65
−0.74
0.32
0.41

0.22
8.25
−1.65
−0.75
0.32
0.41

Panel C: Mean Excess Return of 16%

Uncon

Short sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

0

Growth

Value

Small

Large

Low

Med

High

<0.2

<0.5

<1

Weight, abs.val.(%)
Max weight (%)
Min weight (%)
Short weights
Short fraction
Turnover

0.28
6.10
−3.02
−1.12
0.30
0.76

0.15
4.16
−1.25
−0.37
0.22
0.53

0.08
5.24
0.00
0.00
0.00
0.42

0.48
4.35
−3.80
−1.14
0.31
0.70

0.40
4.70
−3.18
−0.40
0.18
0.72

0.48
5.67
−2.59
−0.74
0.34
0.64

0.52
5.44
−4.48
−1.10
0.39
0.79

0.21
1.68
−2.18
−0.69
0.30
0.51

0.20
1.62
−2.02
−0.62
0.29
0.48

0.20
1.55
−1.83
−0.60
0.31
0.47

–
–
–
–
–
–

0.21
2.84
−2.77
−0.69
0.27
0.40

0.28
6.08
−3.02
−1.11
0.30
0.75

### 5.3. Measuring mutual fund performance and rank

In this section, we analyze an essential question. If fund benchmarks were properly adjusted to account for mandates and
constraints facing the funds, thus, allowing an apples-to-apples comparison — how would this impact the distribution and rank
of relative performance of mutual funds? Said differently, how is the cross-section of relative fund performance altered, if at all,
when properly accounting for mandates and constraints?

We illustrate our procedure of building the requisite bespoke skill distribution by first providing two single fund examples to
highlight how we account for individual mandates and constraints. Specifically, we use the Value Line Large Companies Fund and the
Janus Investment Fund as our examples because they span the entire sample period (January 1974 to December 2013) and they both
face a broad set of mandates and constraints. The Value Line Fund is a large-cap fund with December 2013 AUM of $0.21B and the
S&P 500 as its chosen benchmark; the Janus Fund is a value fund with December 2013 AUM of $1.75B and the FTSE EPRA/NAREIT
Developed and Global Indices as its chosen benchmark.

We begin by considering the unconstrained benchmark coupled with the risk-free asset, then we sequentially account for
mandates and constraints, adding a single additional constraint in each successive step. Because the contribution of each constraint
to the shift in the minimum variance frontier is not independent, we fix the order that constraints will be addressed. Specifically,
the constraint ordering we employ is: investment universe, borrowing/lending, short-sale, turnover, and transaction costs.10

Chart 7 illustrates how mandates and constraints are incorporated to sequentially create the bespoke benchmarks, Panel A
displays the Value Line Fund and Panel B displays the Janus Investment fund. A number of interesting results emerge from this simple
comparison. First, the impact of mandates and constraints can be very different across individual funds. For example, consider
the mandate to be fully-invested with a zero-cash balance (the second adjustment from the benchmark). The adjustment for the
Janus Investment Fund is much larger than the adjustment for the Value Line Large Companies Fund, likely due to the more illiquid
nature of value stocks. Second, if the difference between the standard deviations of a benchmark and the two sample funds is
smaller, then we observe that this difference relative to the bespoke benchmark adjusted for mandates and constraints is higher in
both cases. Lastly, the performances of the two funds diverge from each other (namely, have a wider spread) after adjusting for
mandates and constraints. Relative to the unconstrained benchmark, the fund performances are -13% and -11%, respectively (200

10 We perform robustness checks on the ordering of our mandates and constraints, and while the estimates vary slightly, the results are both quantitatively

and qualitatively similar and are available upon request.

86

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 4
Impact on Trading Strategies for the In-Sample Constrained Parametric Model. This table presents the coefficients regarding the constrained parametric
portfolio weights given the target mean excess return of 8% p.a. Panel A shows the coefficients for the market and sector-level beta strategies, Panel B for the
firm-level beta strategies, Panel C for the sector-level alpha strategies, and Panel D for the firm-level alpha strategies.

Panel A: Coefficients for market and sector-level beta strategies

Benchmark

Short-sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

0

growth

value

small

large

low

med

high

<0.2

<0.5

<1

Small-Growth
ME
BTM
MOM

Small-Value
ME
BTM
MOM

Large-Growth
ME
BTM
MOM

Large-Value
ME
BTM
MOM

0
0.155
0

0
0
0

0
0.254
0

0
0.427
0

0
0.196
0

0
0.189
0

0
0.226
0

0
0
0

0
0.186
0

0
0.431
0

0
0
0

0
0.014
0.129

0
0.417
0.072

0
0
0

0
0.297
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0.527
0.001

0
0.801
0

0
0.002
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0.207
0

0
0.442
0

0
0.120
0

0
0.089
0

0
0.059
0

0
0.142
0

0
0.155
0

0
0.155
0

0
0
0

0
0.115
0

0
0.192
0.006

0
0
0

0
0.083
0

0
0.131
0.009

0
0
0

0
0.059
0

0
0.086
0.010

0
0
0

0
0.052
0

0
0.370
0

0
0
0

0
0.254
0

0
0.427
0

0
0
0

0
0.254
0

0
0.427
0

Panel B: Coefficients for firm-level beta strategies

Benchmark

Short-sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

Small-Growth
ME
BTM
MOM

Small-Value
ME
BTM
MOM

Large-Growth
ME
BTM
MOM

Large-Value
ME
BTM
MOM

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0

0
0
0

0.180
0
0

0
0
0

0
0
0

growth

value

small

large

low

med

high

<0.2

<0.5

<1

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0.088
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0.020
0
0

0.059
0
0

0.075
0
0

0
0
0

0
0
0

0.038
0
0

0.080
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

(continued on next page)

basis point difference), while relative to the bespoke constrained benchmark the performances are −6.1% and −2.7% (340 basis

points difference), respectively.

With our two examples as a backdrop, we turn our attention to constructing the full sample distribution of bespoke performance

levels and fund rankings. Note that to be included in this analysis we require our sample funds to have a minimum of 10 years

of data. We adopt this investment horizon screen to focus attention on fund performance over the long-run. This screen results

in 71 funds with which we repeat the process applied to the example funds above, namely, we estimate the parameters of the

unconstrained and constrained portfolio policies by matching the time-series of the fund return and the market data.

To facilitate our assessment of fund performance, we define two comparison metrics. The first is excess risk defined as 𝜎𝑖 − 𝜎𝑏,
where 𝜎𝑖 is the standard deviation of fund 𝑖’s excess returns and 𝜎𝑏 is the standard deviation of the benchmark portfolio’s excess
𝜎𝑖−𝜎𝑏
, where the numerator is the excess risk metric defined above and
returns. The second is the return-adjusted excess risk defined as
𝜇𝑖
𝜇𝑖 is the mean excess return of fund 𝑖. The return-adjusted excess risk effectively measures the excessive risk per unit of expected

87

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 4 (continued).

Panel C: Coefficients for sector-level alpha strategies

Benchmark

Short-sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

Small-Growth
ME
BTM
MOM

Small-Value
ME
BTM
MOM

Large-Growth
ME
BTM
MOM

Large-Value
ME
BTM
MOM

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0

0
0
0

0
0
0

0
0
0

0
0
0

growth

value

small

large

low

med

high

<0.2

<0.5

<1

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0.009

0
0
0.001

0
0
0.004

0
0
0

0
0
0.009

0
0
0.004

0
0
0.003

0
0
0

0
0
0.005

0
0
0.004

0
0
0.003

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0
0

Panel D: Coefficients for firm-level alpha strategies

Benchmark

Short-sale

Universe

Transaction cost

Turnover

w/o rf

<0.5

Small-Growth
ME
BTM
MOM

Small-Value
ME
BTM
MOM

Large-Growth
ME
BTM
MOM

Large-Value
ME
BTM
MOM

0
0.413
0

0.318
0
0.044

0
0
0.036

0
0
0.065

0
0.371
0

0.003
0
0.045

0
0
0.066

0
0
0.015

0

0
0
0

0
0
0

0
0
0

0
0
0

growth

value

small

large

low

med

high

<0.2

<0.5

<1

0
0.500
0

0
0
0

0
0
0

0.306
0
0.020

0
0.046
0.074

0
0
0

0
0
0

0
0
0.167

0
0.268
0

0.004
0
0

0
0
0

0
0
0

0
0
0

0
0
0

0
0.397
0.140

0
0
0.085

0
0.252
0

0.178
0
0.041

0
0.098
0

0
0
0.021

0
0.174
0

0.107
0
0.027

0
0.085
0

0
0
0.014

0
0.095
0

0.030
0
0.021

0
0.055
0

0
0
0.009

0
0.278
0

0
0
0

0
0
0

0
0
0

0
0.413
0

0.318
0
0.044

0
0
0.036

0
0
0.065

0
0.413
0

0.318
0
0.044

0
0
0.036

0
0
0.065

excess return and can be interpreted as the additional risk the fund manager needs to take for each percentage point of expected
excess return earned by the fund.11

Our fund performance results are presented in Chart 8 and Table 5. Chart 8 displays the distribution of return-adjusted excess
risk measured against the original and bespoke benchmarks and Table 5 displays the associated statistical comparisons between the
two distributions. Chart 8 shows a dramatic shift in the distribution of return-adjusted excess risk toward zero, suggesting far less
under-performance relative to their bespoke benchmarks than implied by the original benchmarks. Table 5 compares the moments
of the two distributions. The results show a monotonic and statistically significant reduction in fund underperformance (mean) for
both metrics with the inclusion of each additional mandate and constraint. In addition, the standard deviation of both metrics tends
to increase with each added mandate and constraint, which suggests more of a performance discrepancy between funds than was
previous appreciated. Skewness and kurtosis are more ambiguous, although there appears to be less skewness and kurtosis for the
bespoke distribution of return-adjusted excess risk.

As the distribution of fund performance is altered with bespoke benchmarks, is it natural to hypothesize that the relative rank of
funds would also change. Chart 9 displays the bespoke performance rankings and those rankings based on traditional performance for

11 We present the differences in terms of risk, instead of the more common return (alpha) approach, for two reasons. First, changing the minimum-variance
optimization to maximize return given risk poses an estimation challenge in that it penalizes highly constrained portfolios (e.g., no leverage, no short-sale, low
turnover) to achieve a high risk target. Second, comparisons of Sharpe Ratios are also problematic, as managers with higher target return would be labeled as
less skilled.

88

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 6. Comparison of in-sample and out-of-sample model performance. This series of charts compares the standard deviation, average excess return, and
Sharpe ratio results within the in-sample and out-of-sample bespoke model estimations. The in-sample estimation is conducted over the period January 1974
through December 2013 while the initial out-of-sample estimation is conducted over the period January 1964 through December 1973 and then re-estimated
recursively through December 2013, adding one month of data each iteration.

our sample of 71 funds partitioned into the four fund subgroups, large, small, growth and value, in panels A through D, respectively.
As above, performance is measured as return-adjusted excess risk.12 The chart is constructed so the diagonal represents the original
rankings of funds and the vertical bars represent the bespoke rankings; thus, bars above (below) the diagonal represent a rank
improvement (deterioration) with the bespoke benchmark. The results include a number of noteworthy observations. First, the
bespoke rankings are statistically different for all subgroups. In particular, tests of the equality of matched pairs of observations
using the Wilcoxon matched-pairs signed-ranks test can be rejected at the 1% level for each group. Second, of the four groups, the
large-capitalization funds display the least change in the rankings, likely because the stock universe is small and liquidity ample

12 While rankings based on risk-adjusted returns are theoretically appropriate, we acknowledge that market participants traditionally measure performance
rank as a simple return difference between the fund and respective benchmark. As a robustness check we have compared the simple return differential rank
with the bespoke rank and the results are both quantitatively and qualitatively similar to those shown.

89

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 7. Examples of imposing fund-specific mandates and constraints. This chart provides two examples of imposing fund-specific mandates and constraints
on the minimum-variance frontier and the resulting implied skill level of the manager. Each panel illustrates a series of bespoke benchmarks that are applicable
to our example funds. Panel A details the Value Line Large Companies Fund, which is a large-capitalization fund with December 2013 AUM of $0.21B and the S&P
500 as its chosen benchmark. Panel B shows the Janus Investment Fund, which is a value fund with December 2013 AUM of $1.75B and the FTSE EPRA/NAREIT
Developed and Global indices as its chosen benchmark.

Chart 8. Comparison of standard and bespoke fund performance. The following chart compares fund performance measured against the standard
(unconditional) benchmark to the bespoke benchmark for 71 of the sample funds that had at least a 10-year track record. The bespoke benchmark for each fund
was estimated imposing the fund-specific constraints applicable to that fund. We define two comparison metrics; the first is return-adjusted excess risk defined
as 𝜎𝑖 −𝜎𝑏
, where 𝜇𝑖 is the mean excess return of fund 𝑖. The return-adjusted excess risk effectively measures the excessive risk per unit of expected excess return
𝜇𝑖
and can be interpreted as the amount of additional risks the fund manager needs to take for each percentage point of the expected excess return earned by the
manager.

90

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Table 5
Comparison of Standard and Bespoke Skill Distributions. We define two comparison metrics the first is excess risk defined 𝜎𝑖 − 𝜎𝑏 , where 𝜎𝑖 is the standard
deviation of fund 𝑖’s excess returns and 𝜎𝑏 is the standard deviation of excess returns to the benchmark portfolio, the second is return-adjusted excess risk defined
as 𝜎𝑖 −𝜎𝑏
, where 𝜇𝑖 is the mean excess return of fund 𝑖. The return-adjusted excess risk effectively measures the excessive risk per unit of expected excess return
𝜇𝑖
and can be interpreted as the amount of additional risks the fund manager needs to take for each percentage point of the expected excess return earned by the
manager. Mandate and constraints, 1 through 4, are: Investment universe (size and style), cash holding and leverage, short-sale, and turnover, respectively.

Panel A: Summary Statistics of Performance Metrics

Metrics

Unconstrained

Bespoke with mandates and constraints:

Excess Risk
Mean
Std. Dev.
Skew
Kurtosis

Return-adjusted excess risk
Mean
Std. Dev.
Skew
Kurtosis

14.39
4.16
0.40
3.23

2.37
2.02
2.56
9.57

1

12.49
4.91
0.42
2.79

2.13
2.05
2.49
9.22

1 + 2

10.71
6.02
0.25
2.42

1.92
2.16
2.32
8.42

1 + 2 + 3

1 + 2 + 3 + 4

9.92
6.07
0.32
2.46

1.82
2.12
2.21
7.76

8.51
6.53
0.52
2.32

1.67
2.18
2.18
7.55

Panel B: Significance of Bespoke Benchmarking on Fund Manager Skills

Metrics

Unconstrained

Bespoke with mandates and constraints:

Excess Risk
𝐿𝑒𝑣𝑒𝑙

𝐶ℎ𝑎𝑛𝑔𝑒

14.39*

Return-adjusted excess risk
𝐿𝑒𝑣𝑒𝑙

2.37*

𝐶ℎ𝑎𝑛𝑔𝑒

*Indicates statistical significance at the level of 1%.

1

1 + 2

1 + 2 + 3

1 + 2 + 3 + 4

12.49*

−1.90*

2.13*

−0.25*

10.71*

−1.77*

1.92*

−0.21*

9.92*

−0.80*

1.82*

−0.09*

8.51*

−1.41*

1.67*

−0.15*

relative to the other groups. Third, ranking changes appear to be concentrated at the top of the rankings (best) rather than at the
bottom, perhaps because the performance differential among funds is decreasing with rank. The most substantial change occurs
within the rank of the top three funds for small, growth and value, with the highest ranked fund changing for small and value. As
an example, consider the value group in Panel D. The top two funds in the original ranking were the Third Avenue Value Fund
($2.55B AUM, MSCI World Index as benchmark) and the Franklin Balance Sheet Investment Fund ($1.72B AUM, Russell 3000 Value
Index as benchmark), respectively. After taking account of individual fund mandates and constraints, the Third Avenue Value Fund
falls to third, the Franklin Balance Sheet Investment Fund remains second and the Gabelli Value Fund ($0.64B AUM with S&P500
as benchmark) takes over the top-ranked spot moving up from fourth place.

The Janus and Value Line Fund examples and altered fund rankings put in clear view the statistically and economically significant
impact of mandates and constraints on mutual fund performance. We acknowledge that while mutual fund constituencies universally
want accurate performance assessments, their interest in accurately measuring the components, mandates/constraints and manager
skill, is predicated on whether they take mandates and constraints as exogenous or endogenous with respect to their goal or objective.
Mutual fund advisors and fund board of directors necessarily take fund mandates and constraints as fixed rules within which
the fund manager must operate and are therefore exogenous to the objectives of performance-based compensation and the relative
value-add of the advisor’s management, respectively. Consider a mutual fund advisor’s objective of compensating and retaining
skillful portfolio managers. Since mandates and constraints are specified in the fund prospectus and very rarely, if ever change,
the fund advisor would want to retain and reward/compensate portfolio managers who exhibit skill within the mutual fund’s given
mandates and constraints. Indeed, the fund advisor would prefer to employ the portfolio manager with the highest skill among the
set of portfolio managers that operate within that investing environment. Hence, from a compensation and retention standpoint fund
performance should be measured abstracting from the inherent characteristics of the fund that are captured in its mandates and
constraints. Indeed, the findings of Khorana (1996) and Daniel et al. (1997) are consistent with measuring performance based on
fund manager skill, rather than exogenous factors impacting performance. In addition, anecdotally, a Chief Investment Officer (CIO)
of a prominent fund family acknowledged that despite the externally visible constraints in the prospectus, portfolio managers are
compensated, not by their performance relative to the public benchmarks, but by their internal benchmark model which is subject
to the constraints they impose on each manager to measure their alpha generation through stock selection on top of constraints
factor exposure.

Mutual fund board members have a similar perspective whereby mandates and constraints are rarely considered a choice variable
instead being treated as exogenous with respect to their fiduciary responsibility to ensure the value/performance delivered is
appropriate for the fees charged. The Investment Company Act of 1940 requires that mutual fund board of directors annually

91

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

Chart 9. Change in group rankings based on bespoke benchmark performance. The following chart compares fund rankings based on bespoke performance
and rankings based on traditionally-measured performance for our sample of 71 funds partitioned by large-cap, small-cap, growth and value groups respectively.
The diagonal line in each panel represents the group ranking based on traditionally-measured performance and the vertical bars represent the rankings based the
bespoke performance. Tests of the equality of matched pairs of observations for each group using the Wilcoxon matched-pairs signed-ranks test can be rejected
at the 1% level.

review and approve the fund advisory contract. The fund directors are specifically asked to consider a number of factors, known as
the Gartenberg Factors after the current precedent setting legal case, when making their determination. Specifically, directors must
consider and evaluate: (1) the nature, extent, and quality of the services provided by the advisor, including the investment process
used by the advisor; (2) the performance of the funds in comparison to their benchmark indices and a peer group of mutual funds; (3)
the management fees and total operating expenses of the funds, including comparative information with respect to a peer group of
mutual funds; (4) the profitability of the advisor with respect to the funds; and (5) the extent to which economies of scale may be
realized as the funds grow. The proper evaluation of each of these Gartenberg Factors necessitates assessing the value provided the
shareholder by the advisor abstracting from the impact of the mandates and constraints imposed on the fund. Consistent with the
need for directors to focus on manager skill in conducting their review, research by Ding and Wermers (2012) provide evidence that
funds with superior ‘‘internal governance’’ are better able to monitor performance and terminate underperforming, inexperienced
managers. Thus, from a practical perspective for the fund advisor and a regulatory perspective for the fund board of directors, the
importance of being able to properly assess the performance of a mutual fund abstracting from the exogenously given mandates
and constraints can hardly be overstated.

## 6. Conclusion

We develop a methodology to incorporate frictions into financial settings where heretofore their impact could not be quantified.
We apply our methodology to the lingering academic quandary regarding the appropriateness of comparing mutual fund perfor-
mance to a benchmark that does not share the same mandates and constraints. The approach utilizes a parametric re-mapping
of portfolio weights having imposed individual fund mandates and constraints. Our results demonstrate that fund mandates and
constraints are pervasive and impose costs on funds that are economically important. Consistent with their importance, they impact
both fund portfolio weights and manager trading strategies.

By constructing bespoke benchmarks for a sample of mutual funds, we are able to improve on the performance evaluation of
mutual funds and their relative ranking. A comparison of fund performance relative to its appropriate bespoke benchmark within our

92

A. Beber, M.W. Brandt, J. Cen et al.

Journal of Empirical Finance 60 (2021) 74–93

sample shows a monotonic increase in relative performance with the inclusion of each additional mandate and constraint, where the
aggregate increase is between 30 and 40%. More important than the increase in relative performance is the change in the ranking
of peer funds. Performance rankings that account for fund mandates and constraints are significantly and economically different
than traditional rankings which fail to do so. Funds investing in small-cap, growth and value display the largest ranking changes,
particularly for the top ranked funds. Armed with these bespoke rankings, mutual fund advisors and board of directors would likely
make different decisions suggesting an improved allocation of capital and oversight among mutual funds.

From the practitioner’s perspective, our results are important for mutual fund advisors/management and fund directors/boards.
For mutual fund advisors/management should be evaluating portfolio managers based on mandate/constraint adjusted performance
for compensation and retention purposes. In addition, in order for mutual fund directors/boards to execute their fiduciary
responsibility to their shareholders, they should be comparing the fund advisor’s performance against an appropriate bespoke
benchmark during their annual 15(c)-3 review of the fund’s advisory contract.

## References

Blake, C., Morey, M., 2000. Morningstar ratings and mutual fund performance. J. Financ. Quant. Anal. 35, 451–483.
Brandt, M., Santa-Clara, P., Valkanov, R., 2009. Parametric portfolio policies: Exploiting characteristics in the cross-section of equity returns. Rev. Financ. Stud.

22, 3411–3447.

Briere, M., Szafarz, A., 2017. In: Jurczenko, E. (Ed.), Factor Investing: The Rocky Road from Long Only to Long Short in Factor Investing. ISTE Press Ltd.
Cremers, M., Fulkerson, J., Riley, T., 2018. Benchmark Discrepancies and Mutual Fund Performance Evaluation. University of Notre Dame, Working Paper.
Daniel, K., Grinblatt, M., Titman, S., Wermers, R., 1997. Measuring mutual fund performance with characteristic-based benchmarks. J. Finance 52, 1035–1058.
Del Guercio, D., Tkac, P., 2008. Star power: The effect of morningstar ratings on mutual fund flow. J. Financ. Quant. Anal. 43, 907–936.
Ding, B., Wermers, R., 2012. Mutual Fund Performance and Governance Structure: The Role of Portfolio Managers and Board of Directors. University of Maryland,

Working Paper.

Friesen, G., Nguyen, V., 2018. The Economic Impact of Mutual Fund Investor Behaviors. University of Nebraska, Working Paper.
Khorana, A., 1996. Top management turnover an empirical investigation of mutual fund managers. J. Financ. Econ. 40, 403–427.
Mateus, I., Mateus, C., Todorovic, N., 2017. The Impact of Benchmark Choice on US Mutual Fund Benchmark-Adjusted Performance and Ranking. University of

Greenwich, Working Paper.

Palmiter, A., 2016. The mutual fund investor. In: Elgar HandBook of Mutual Fund Regulation. http://dx.doi.org/10.2139/ssrn.2853506, (forthcoming).
Sensoy, B., 2009. Performance evaluation and self-designated benchmark indexes in the mutual fund industry. J. Financ. Econ. 92, 25–39.

93

