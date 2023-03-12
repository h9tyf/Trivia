import os
from flask import Flask, request, abort, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from  sqlalchemy.sql.expression import func, select
from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE 
    end = start + QUESTIONS_PER_PAGE 

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def paginate_categories(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE 
    end = start + QUESTIONS_PER_PAGE 

    categories = [category.format() for category in selection]
    current_categories = categories[start:end]

    return current_categories


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)
    
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response


    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        res = [category.format() for category in categories]
        return jsonify({
            'success': True,
            'categories': res,
            'total_categories': len(res)
        })


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(Question.query.all()),
                "currentCategory": 1, # ??????
                "categories": [category.format() for category in Category.query.all()]
            }
        )

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
        except:
            abort(400)

        if question is None:
            abort(404)

        question.delete()
        db.session.commit()

        return jsonify({
                "success": True,
                "deleted": question_id
            })
        

    @app.route("/questions", methods=["POST"])
    def create_question():
        body = request.get_json()
        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_difficulty = body.get("difficulty", None)
        new_category = body.get("category", None)
        search_term = body.get("searchTerm", None)

        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search_term))
                )
                current_questions = paginate_questions(request, selection)
                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "totalQuestions": len(current_questions), # ????
                        "currentCategory": "?"
                    }
                )
            else:
                question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
                question.insert()
                db.session.commit()

                return jsonify(
                    {
                        "success": True,
                        "created": question.id
                    }
                )
        except:
            abort(422)

    
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        questions = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)

        if len(questions) == 0:
            abort(404)
        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "totalQuestions": len(current_questions),
                "currentCategory": category_id
            }
        )


    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()

        prev_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        question = Question.query.filter(Question.category == quiz_category)\
            .filter(Question.id.notin_(prev_questions)).order_by(func.random()).one_or_none()

        if question == None:
            abort(404)

        return jsonify(
            {
                "success": True,
                "question": question.format()
            }
        )



    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404
        

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400


    return app

