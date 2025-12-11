"""
Flask app to serve Forex Factory news CSV files.
"""
import os
from flask import Flask, send_file, jsonify
from datetime import datetime
import subprocess
import scraper

app = Flask(__name__)
NEWS_DIR = os.path.join(os.path.dirname(__file__), 'news')


@app.route('/', methods=['GET'])
def home():
    """Home route with available endpoints."""
    return jsonify({
        'message': 'Forex Factory News Scraper API',
        'endpoints': {
            '/csv/<month>/<year>': 'Get CSV for a specific month/year (e.g., /csv/December/2025)',
            '/csv/current': 'Get CSV for current month',
            '/csv/list': 'List all available CSV files',
            '/scrape': 'Run scraper for current month (POST request)',
            '/scrape/<months>': 'Run scraper for specific months (POST request, e.g., /scrape/this/next)',
        }
    })


@app.route('/csv/<month>/<year>', methods=['GET'])
def get_csv(month, year):
    scraper.scrape_news_for_month()
    """Serve a CSV file for a specific month and year."""
    filename = f"{month}_{year}_news.csv"
    filepath = os.path.join(NEWS_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': f'CSV file not found: {filename}'}), 404
    
    return send_file(filepath, as_attachment=True, mimetype='text/csv')


@app.route('/csv/current', methods=['GET'])
def get_current_csv():
    """Serve CSV for the current month."""
    scraper.scrape_news_for_month()
    now = datetime.now()
    month = now.strftime("%B")
    year = now.strftime("%Y")
    
    filename = f"{month}_{year}_news.csv"
    filepath = os.path.join(NEWS_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': f'CSV file not found for current month: {filename}'}), 404
    
    return send_file(filepath, as_attachment=True, mimetype='text/csv')


@app.route('/csv/list', methods=['GET'])
def list_csv_files():
    #scraper.scrape_news_for_month()
    """List all available CSV files."""
    if not os.path.exists(NEWS_DIR):
        return jsonify({'csv_files': [], 'message': 'No CSV files found'}), 200
    
    csv_files = [f for f in os.listdir(NEWS_DIR) if f.endswith('.csv')]
    csv_files.sort(reverse=True)
    
    return jsonify({
        'count': len(csv_files),
        'csv_files': csv_files
    })


@app.route('/scrape', methods=['POST'])
def scrape_current():
    """Run scraper for the current month."""
    try:
        result = subprocess.run(
            ['python', 'scraper.py'],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            now = datetime.now()
            month = now.strftime("%B")
            year = now.strftime("%Y")
            filename = f"{month}_{year}_news.csv"
            
            return jsonify({
                'success': True,
                'message': f'Scraper completed successfully',
                'output': result.stdout,
                'filename': filename
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Scraper timed out (5 minutes)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scrape/<path:months>', methods=['POST'])
def scrape_months(months):
    """Run scraper for specific months (comma or slash separated)."""
    try:
        # Convert comma or slash separated values to space-separated for CLI
        month_list = months.replace(',', ' ').replace('/', ' ').split()
        
        result = subprocess.run(
            ['python', 'scraper.py', '--months'] + month_list,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Scraper completed successfully for: {", ".join(month_list)}',
                'output': result.stdout,
                'months': month_list
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Scraper timed out (5 minutes)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found', 'path': str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
