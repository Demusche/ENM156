# Author: Salam Hani
print(1)
import sys
print(2)
import os
print(3)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
print(4)
from flask import *
print(5)
import calculate
print(6)
app = Flask(__name__)


@app.errorhandler(Exception)
def handle_exception(err):
  path = request.path

# This is the route when clicking the link on index.html
@app.route('/calculate', methods=['GET'])
def main_function():
  
    Capacity = float(request.args.get('Capacity'))
    Buffersize = float(request.args.get('BufferSize'))
    Maxcharge = float(request.args.get('MaxCharge'))
    Mincharge = float(request.args.get('MinCharge'))
    DepthOfDischarge = float(request.args.get('dod'))
    Power = float(request.args.get('Power'))
    answer = calculate.calculate(Capacity, Buffersize, Mincharge, Maxcharge, DepthOfDischarge, Power)
    answer2, (answer3, answer4) = calculate.calculate_peak(Capacity, Buffersize, Mincharge, Maxcharge, DepthOfDischarge, Power)
    return jsonify({'FCRD_array': answer,
                    'Peak_savings': answer2,
                    'Old_usage': answer3,
                    'New_usage': answer4})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug="True")
