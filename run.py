from utils.data_loader import load_data
from strategies.sma_crossover import generate_signals
from backtests.engine import run_backtest
from utils.performance import calculate_metrics
import matplotlib.pyplot as plt


def main():
    data = load_data("AAPL")
    signals = generate_signals(data)
    results = run_backtest(signals)

    metrics = calculate_metrics(results)

    print("Performance Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    # 🔥 Plot INSIDE main
    plt.figure(figsize=(10,5))
    plt.plot(results["equity_curve"], label="Strategy")
    plt.plot(results["buy_hold_equity"], label="Buy & Hold")
    plt.legend()
    plt.title("Strategy vs Buy & Hold")
    plt.show()


if __name__ == "__main__":
    main()``