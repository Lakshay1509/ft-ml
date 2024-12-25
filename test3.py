import pandas as pd
from datetime import  datetime

def preprocess_data(transactions):
    transactions.dropna(subset=['date', 'amount'], inplace=True)
    transactions['date'] = pd.to_datetime(transactions['date'], errors='coerce')
    transactions.dropna(subset=['date'], inplace=True)
    transactions['month'] = transactions['date'].dt.month
    transactions['day'] = transactions['date'].dt.day
    transactions['amount_spent'] = transactions['amount'].apply(lambda x: abs(x) if x < 0 else 0)
    return transactions

def analyze_spending(transactions, category_limits):
    current_month = transactions['month'].max()
    current_year = transactions['date'].dt.year.max()
    if current_month == 12:
        next_year, next_month = current_year + 1, 1
    else:
        next_year, next_month = current_year, current_month + 1

    days_in_month = (datetime(next_year, next_month, 1) - datetime(current_year, current_month, 1)).days
    transactions_current_month = transactions[transactions['month'] == current_month]

    # Monthly analysis
    category_spending = transactions_current_month.groupby('categoryId')['amount_spent'].sum().reset_index()
    category_spending.rename(columns={'amount_spent': 'total_spent'}, inplace=True)
    category_spending['monthly_limit'] = category_spending['categoryId'].map(category_limits).fillna(0)

    today = datetime.now()
    if today.year == current_year and today.month == current_month:
        days_elapsed = (today - datetime(current_year, current_month, 1)).days + 1
    else:
        days_elapsed = transactions_current_month['day'].max()

    days_remaining = days_in_month - days_elapsed
    category_spending['avg_daily_spent'] = category_spending['total_spent'] / days_elapsed
    category_spending['savings_needed'] = (
    category_spending['avg_daily_spent'] * days_in_month - category_spending['monthly_limit']
    )
    category_spending['savings_needed'] = (
        category_spending['avg_daily_spent'] * days_in_month - category_spending['monthly_limit']
    )
    category_spending['daily_saving_suggestion'] = category_spending['savings_needed'] / days_remaining
    category_spending.loc[category_spending['savings_needed'] <= 0, 'daily_saving_suggestion'] = 0
    # category_spending.to_csv('analysis_output.csv', index=False)

    
    category_spending = category_spending[
        ['categoryId', 'total_spent', 'avg_daily_spent', 'monthly_limit','savings_needed' ,'daily_saving_suggestion']
    ]

    # 5-Day analysis
    past_5_days = transactions_current_month[
        transactions_current_month['date'] >= transactions_current_month['date'].max() - pd.Timedelta(days=5)
    ]
    last_5_days_spending = past_5_days.groupby('categoryId')['amount_spent'].sum().reset_index()
    last_5_days_spending.rename(columns={'amount_spent': 'total_spent'}, inplace=True)
    last_5_days_spending['avg_daily_spent'] = last_5_days_spending['total_spent'] / 5
    last_5_days_spending = pd.merge(
        last_5_days_spending, category_spending[['categoryId', 'monthly_limit']],
        on='categoryId', how='left'
    )
    last_5_days_spending['savings_needed'] = last_5_days_spending['total_spent'] - last_5_days_spending['monthly_limit']
    last_5_days_spending['daily_saving_suggestion'] = last_5_days_spending['savings_needed'] / 5
    last_5_days_spending.loc[last_5_days_spending['savings_needed'] <= 0, 'daily_saving_suggestion'] = 0
    
    last_5_days_spending = last_5_days_spending[
        ['categoryId', 'total_spent', 'avg_daily_spent', 'monthly_limit', 'daily_saving_suggestion']
    ]

    # Higher than usual analysis
    transactions['week'] = transactions['date'].dt.isocalendar().week
    current_week = transactions['week'].max()
    current_week_transactions = transactions[transactions['week'] == current_week]
    past_week_transactions = transactions[transactions['week'] == current_week - 1]

    past_week_spending = past_week_transactions.groupby('categoryId')['amount_spent'].sum().reset_index()
    past_week_spending.rename(columns={'amount_spent': 'past_week_spent'}, inplace=True)

    current_week_spending = current_week_transactions.groupby('categoryId').agg(
        current_spent=('amount_spent', 'sum'),
        days_count=('day', 'nunique')
    ).reset_index()
    current_week_spending['projected_spent'] = (
        current_week_spending['current_spent'] / current_week_spending['days_count'] * 7
    )

    weekly_comparison = pd.merge(past_week_spending, current_week_spending, on='categoryId', how='outer').fillna(0)
    weekly_comparison['higher_than_usual'] = (
        weekly_comparison['projected_spent'] > 1.35 * weekly_comparison['past_week_spent']
    )

    return {
        "monthly_analysis": category_spending.to_dict(orient='records'),
        "five_day_analysis": last_5_days_spending.to_dict(orient='records'),
        "higher_than_usual": weekly_comparison.to_dict(orient='records')
    }

def main():
    # Load transactions data
    transactions = pd.read_csv('transactions.csv')
    transactions = preprocess_data(transactions)

    # Define category limits and importance levels
    category_limits = {
        'category_1': 5000,
        'category_2': 10000,
        'category_3': 7000,
        'category_4': 1000
    }
    
    # Perform analysis
    results = analyze_spending(transactions, category_limits)

    # Display results
    print("Monthly Spending Analysis:")
    print(pd.DataFrame(results['monthly_analysis']))

    print("\nLast 5 Days Spending Analysis:")
    print(pd.DataFrame(results['five_day_analysis']))

    print("\nHigher Than Usual Spending Analysis:")
    print(pd.DataFrame(results['higher_than_usual']))

if __name__ == "__main__":
    main()