import backtrader as bt
import pandas as pd

from strategy import SMAStrategy    

if __name__ == "__main__":
    cerebro = bt.Cerebro()
    
    # Load data
    dataframe = pd.read_csv(
        "data/AAPL_last_season.csv",
        parse_dates=['Date']
    )

    dataframe.set_index('Date', inplace=True)
    # Dynamically determine fromdate and todate
    fromdate = dataframe.index.min().to_pydatetime()
    todate = dataframe.index.max().to_pydatetime()
    # Map CSV columns to Backtrader fields
    data_feed = bt.feeds.PandasData(
        dataname=dataframe,
        fromdate=fromdate,
        todate=todate,
        timeframe=bt.TimeFrame.Days,
        open='Open',
        high='High',
        low='Low',
        close='Close',
        volume='Volume'
    )

    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(SMAStrategy)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # Set broker parameters
    cerebro.broker.setcash(100000.0)  # Starting cash
    cerebro.broker.setcommission(commission=0.0006)  # 0.1% commission
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Fixed size of 10 shares

    # Print starting portfolio value
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run backtest
    result = cerebro.run()

    print('sharpe_ratio:', result[0].analyzers.sharpe_ratio.get_analysis())
    print('drawdown:', result[0].analyzers.drawdown.get_analysis()['max']['drawdown']) 

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot results
    cerebro.plot()
    # Plot results
    cerebro.plot()

