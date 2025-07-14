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
  


# 策略

> 第一阶段以低频交易为主
>
> 1. 贴近主观交易：保留“选行业/找主线”的感觉；宏观经济认识；
>
> 2. 又可以用 Python / Pandas / 回测框架跑出历史数据来验证逻辑；
>
> 3. 把“拍脑袋”换成定量的因子系统，各类指标更加明确精准；
> 4. 增强交易纪律性，信号、仓位管理



* 对比估值？两只类似股票，出现估值缺口
* 多因子CTA
  * 复现研报-简单论文

## macky

- [ ] how to define resist & support?
  - [x] 20 days highest / lowest
    - [ ] intervalize
- [ ] breakout
  - [ ] consider resist turn to support when break
- [ ] take profit / stop loss
- [ ] optimization
  - [x] increase trading frequency (30min, 1h)
  - [ ] parameterization (deep-learning)
  - [ ] recognize left side / right side (via news or sth)



| strategy     | info                                                         | perf   | comment                        |
| ------------ | ------------------------------------------------------------ | ------ | ------------------------------ |
| **1.resist** |                                                              |        |                                |
| 1.00         | - use extreme value as resist / support<br />- break -> buy <br />- close after 3 t | -3.81% | - 左侧上涨趋势，会变成追涨杀跌 |
| 1.01         | - signal confirm: break -> observe<br />- candle pattern (strength index) |        |                                |
| 1.02         | - define resist/support as stack                             |        |                                |
| 1.03         | - when breakout -> buy; reject -> sell                       |        |                                |



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





# 回测

- [ ] calc beta
- [ ] minute-level backtest



# 学习资源

| --     | --                                                           |
| ------ | ------------------------------------------------------------ |
| 李不白 | [bilibili](https://space.bilibili.com/3546791769279104?spm_id_from=333.1387.follow.user_card.click) |
|        | [red](https://www.xiaohongshu.com/user/profile/5f5eeab900000000010047bc?xsec_token=ABuufNWq0rQRznfAUzNjZ6-5ZJYu-DC1GR3Dyn8F34naM%3D&xsec_source=pc_search) |
| 知乎   |                                                              |

