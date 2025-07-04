from flask import Flask, render_template, request, abort
import pickle
import numpy as np
import logging
from functools import lru_cache

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load data with error handling
try:
    popular_df = pickle.load(open('popular.pkl', 'rb'))
    pt = pickle.load(open('pt.pkl', 'rb'))
    books = pickle.load(open('books.pkl', 'rb'))
    similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

    # Get unique book titles for autocomplete
    book_titles = books['Book-Title'].unique().tolist()

except Exception as e:
    logger.error(f"Data loading error: {str(e)}")
    raise RuntimeError("Failed to load data files") from e


@lru_cache(maxsize=1000)
def get_book_details(title):
    try:
        book = books[books['Book-Title'] == title].iloc[0]
        return {
            'title': book['Book-Title'],
            'author': book['Book-Author'],
            'year': book['Year-Of-Publication'],
            'publisher': book['Publisher'],
            'image': book['Image-URL-M'],
            'isbn': book['ISBN']
        }
    except Exception as e:
        logger.error(f"Error getting details for {title}: {str(e)}")
        return None


@app.route('/')
def index():
    try:
        return render_template('index.html',
                               book_data=popular_df.to_dict('records'))
    except Exception as e:
        logger.error(f"Index route error: {str(e)}")
        return render_template('error.html',
                               message="Error loading popular books"), 500


@app.route('/recommend')
def recommend_ui():
    try:
        # Get unique book titles from pivot table index
        book_titles = pt.index.tolist()
        return render_template('recommend.html', book_titles=book_titles)
    except Exception as e:
        logger.error(f"Error loading recommendations UI: {str(e)}")
        return render_template('error.html',
                            message="Error loading recommendation service"), 500

@app.route('/recommend_books', methods=['POST'])
def recommend():
    try:
        user_input = request.form.get('user_input', '').strip()
        if not user_input:
            return render_template('error.html',
                                   message="Please enter a book name"), 400

        if user_input not in pt.index:
            return render_template('error.html',
                                   message="Book not found in database"), 404

        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(enumerate(similarity_scores[index]),
                               key=lambda x: x[1], reverse=True)[1:5]

        data = []
        for i in similar_items:
            try:
                title = pt.index[i[0]]
                book_details = get_book_details(title)
                if book_details:
                    data.append(book_details)
            except Exception as e:
                logger.error(f"Error processing {title}: {str(e)}")
                continue

        return render_template('recommend.html',
                               data=data,
                               book_titles=book_titles)

    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}")
        return render_template('error.html',
                               message="Error generating recommendations"), 500


@app.route('/book/<title>')
def book_details(title):
    try:
        book = get_book_details(title)
        if not book:
            return render_template('error.html',
                                   message="Book details not found"), 404

        # Find purchase options (example implementation)
        book['purchase_links'] = {
            'Amazon': f'https://amazon.com/s?k={book["isbn"]}',
            'eBay': f'https://www.ebay.com/sch/i.html?_nkw={book["isbn"]}'
        }

        return render_template('book_details.html', book=book)
    except Exception as e:
        logger.error(f"Book details error: {str(e)}")
        return render_template('error.html',
                               message="Error loading book details"), 500


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                           message="Internal server error"), 500


if __name__ == '__main__':
    app.run(debug=True)
