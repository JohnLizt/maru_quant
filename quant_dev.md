> 大方向上可以分为alpha、beta两大流派
>
> alpha追求中性，无视市场变化，赚取波动价差，中高频，持有1天以上就算低频了
>
> beta更类似传统主观交易，更加有纪律

# 数据源

| --            | --        |
| ------------- | --------- |
| **free**      |           |
| yfinance      |           |
| alpha vantage | - [ ] asd |
| **charge**    |           |
| tradingview   |           |

- [ ] 支持A股 tushare 下载
  


# CTA主流策略类型

> 1. **趋势跟踪（Trend Following）**
>    - 代表：SMA/EMA突破、Donchian通道、Turtle策略、ADX趋势跟随等
>    - 逻辑：价格突破某一均值或区间后顺势买入/卖出，长期持有趋势单
> 2. **均值回归（Mean Reversion）**
>    - 代表：布林带回归、Keltner通道、价差套利、振荡区间策略
>    - 逻辑：价格偏离均值后，预期其回归历史均值附近
> 3. **套利策略（Arbitrage）**
>    - 代表：跨期套利（Calendar Spread）、跨品种套利、统计套利（Pairs Trading）
>    - 逻辑：利用相关性、价差等市场无效性进行低风险套利
> 4. **动量策略（Momentum）**
>    - 代表：横截面动量（多品种间强者恒强）、时间序列动量（单品种顺势）
>    - 逻辑：近期涨得多的品种继续买入，跌得多的继续卖出
> 5. **反转策略（Reversal）**
>    - 代表：超买超卖反转（如RSI、CCI）、极端事件反转
>    - 逻辑：短期内涨跌过度，预期价格出现反转
> 6. **突破策略（Breakout）**
>    - 代表：区间突破、价格新高新低突破
>    - 逻辑：价格突破一段时间内高点/低点后追随
> 7. **波动率策略（Volatility）**
>    - 代表：基于波动率的波段交易、波动率扩张收缩策略
>    - 逻辑：利用波动率变化进行入场、出场或仓位调整
> 8. **资金管理与组合优化**
>    - 代表：多品种马丁格尔、凯利公式、动态止损止盈等



## **trend following**

> 适用于上涨/下跌行情，震荡市容易出事

### SMA



## event-driven

### LLM-news

* 早鸟策略：新闻发出时快速买入
* 买预期卖事实：在“靴子落地”时，提前布局的主力获利了结，往往有预期反方向的动能



## breakout

> 压力位/支撑位的本质：群体心理学
>
> 参考我自己买日元的经历，第一次碰到4.8没有买，看到涨价到5以上，内心非常后悔，下次价格一触及4.8就会立刻买入。人们对于区域顶部和底部的记忆也是最深刻的。
>
> 压力强度指标也需要考虑，例如双底

- [x] how to define resist & support?
  - [x] extreme value
  - [x] pivot high/low

- [ ] resist / support intensity

- [ ] turn over signal

  - [x] CSI

  - [ ] CISD? wick must be filled, 80%

    > https://www.youtube.com/watch?v=EvG8vRTgRbU&t=3s
    >
    > https://www.bilibili.com/video/BV1D9GLzyEJF/?spm_id_from=333.1007.tianma.1-2-2.click&vd_source=feacdd607007d02479769d9056af2634

  - [ ] consider resist turn to support when break

- [ ] take profit / stop loss

- [ ] trend tracking

  - [ ] recognize left side / right side (via news or sth)

- [ ] optimization
  - [x] trading frequency (30min, 1h)
  - [ ] parameterization
    - [ ] grid tuning
    - [ ] ML / DL



| strategy   | info                                                         | result |        |            | review                       |
| ---------- | ------------------------------------------------------------ | ------ | ------ | ---------- | ---------------------------- |
| **resist** |                                                              | **WR** | **PR** | **profit** | **accuracy & recall**        |
| v1.00      | 1. use extreme value as resist / support<br />2. breakout -> buy / breakdown -> sell <br />3. close after 3 t | -      | -      | -3.81%     | 1. chase rising              |
| v1.01      | 1. break -> observe -> buy + sell<br />2. CSI: candle strength index<br />3. add take profit / stop loss | 33.33% | 1.7    | -0.43%     | 1.resist definition not good |
| v1.02      | 1. pivot: slide windows + monostack<br />                    |        |        |            | 1.too decrete                |
| v1.03      | 1. avoid volatility: news + ATR                              |        |        |            |                              |
| v1.04      | 1. integrate news:<br /> https://www.forexfactory.com/       |        |        |            |                              |



### candles theory

| --           | --            |
| ------------ | ------------- |
| candle wick  | means strong? |
| fill the gap |               |
|              |               |

> ## Candle Strength Index (CSI) — Design Concept
>
> The **Candle Strength Index (CSI)** is an indicator that quantifies the bullish or bearish strength of a single candlestick using only OHLC data (Open, High, Low, Close). Its output ranges from -1 to 1:
>
> - **+1** means very strong bullish candle.
> - **-1** means very strong bearish candle.
> - **0** means neutral, indecisive candle.
>
> ### CSI Formula
>
> CSI is a weighted sum of three components:
>
> 1. **Entity Strength:** Measures the size and direction of the candle body.
> 2. **Close Position Strength:** Measures how close the close price is to the high or low.
> 3. **Shadow Strength (optional):** Measures how much of the candle’s range is taken up by the body.
>
> **Mathematical Representation:**
>
> CSI = α * Entity Strength + β * Close Position Strength + γ * Shadow Strength
>
> Where α, β, γ are weights (e.g., α=0.5, β=0.3, γ=0.2).
>
> #### Component Details
>
> - **Entity Strength:**
>   `(Close - Open) / (High - Low)`
>   Indicates if the candle closed higher (bullish) or lower (bearish), and by how much compared to the candle’s total range.
> - **Close Position Strength:**
>   `((2 * (Close - Low)) / (High - Low)) - 1`
>   Shows how close the close price is to the high (+1) or low (-1).
> - **Shadow Strength:**
>   `1 - (|High - Close| + |Open - Low|) / (High - Low)`
>   Body size relative to the candle’s range; larger body = stronger conviction.
>
> 





## multi factor





# 回测

- [ ] calc beta
- [ ] minute-level backtest



## 学习资源

| --     | --                                                           |
| ------ | ------------------------------------------------------------ |
| 李不白 | [bilibili](https://space.bilibili.com/3546791769279104?spm_id_from=333.1387.follow.user_card.click) |
|        | [red](https://www.xiaohongshu.com/user/profile/5f5eeab900000000010047bc?xsec_token=ABuufNWq0rQRznfAUzNjZ6-5ZJYu-DC1GR3Dyn8F34naM%3D&xsec_source=pc_search) |
| 知乎   |                                                              |

