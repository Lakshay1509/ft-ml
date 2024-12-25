from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from test3 import preprocess_data, analyze_spending

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Parse input JSON data
        data = request.get_json()

        # Ensure 'transactions' and 'category_limits' keys exist
        if 'transactions' not in data or 'category_limits' not in data:
            return jsonify({"error": "Missing required keys in the input data"}), 400

        # Convert transactions to a DataFrame
        transactions_df = pd.DataFrame(data['transactions'])

        # Ensure transactions DataFrame is not empty
        if transactions_df.empty:
            return jsonify({"error": "Transactions data is empty"}), 400

        category_limits_array = data['category_limits']
        category_limits = {item['category']: item['limit'] for item in category_limits_array}

        # Process and analyze data
        transactions_df = preprocess_data(transactions_df)
        results = analyze_spending(transactions_df, category_limits)

        # Prepare response
        response = {
            "monthly_analysis": results.get("monthly_analysis", {}),
            "five_day_analysis": results.get("five_day_analysis", {}),
            "higher_than_usual": results.get("higher_than_usual", {})
        }
        return jsonify(response), 200
    except Exception as e:
        # Catch unexpected errors and return an appropriate response
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
