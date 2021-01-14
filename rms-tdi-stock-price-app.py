from flask import Flask, render_template, request, redirect
import os
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pds
import requests
import simplejson as json
#this list does not seem to be exhaustive, but is the best I could find
#from get_all_tickers import get_tickers as gt
#list_of_all_tickers = gt.get_tickers()

app = Flask(__name__)

@app.route('/')
def subform():
  #landing page with submission form  
  return render_template('subform.html')

@app.route('/image',methods=['GET','POST'])
def image():
    if request.method == 'GET':
        #suggest that users hit up landing page directly
        return render_template("landing_error.html")
    if request.method == 'POST':
        #get stock ticker symbol from submission on landing page
        tickersym = request.form['Name']
        #check if the input is a valid U.S. stock ticker symbol
        if (not tickersym) or tickersym.isdigit(): #or (tickersym not in list_of_all_tickers):
            #suggest that users try again with a recognized ticker symbol
            return render_template("input_error.html")
        else:
            #grab data from alpha vantage
            payload = {'symbol': tickersym}
            r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&apikey=H1ECYNGQQHXUFJMO', params=payload)
            #get data into json format
            data=json.loads(r.text)
            #get data into a Pandas dataframe
            df = pds.DataFrame.from_dict(data)
            #get string to select out the last calendar month of data
            mstr = df.iloc[2,0][5:7]
            def convm(mstr):
                mon = int(mstr) - 1
                if mon != 0:
                    return str(mon) + "-"
                else:
                    return "12-"
            mstr = convm(mstr)
            #data selection
            df = df.reset_index()
            df = df[ df['index'].str.contains(mstr) ].drop(['Meta Data'],axis=1)
            df = df.rename(columns = {'index':'date','Time Series (Daily)': 'price'})
            df['price'] = df['price'].map(lambda x: float(x['5. adjusted close']))
            df['date'] = df['date'].map(lambda x: int(x[8:10]))
            #plot generation
            fig = Figure()
            im = fig.add_subplot(1, 1, 1)
            im.set_xlabel('day of the last month',fontsize = 14, labelpad = 10)
            im.set_ylabel('adjusted closing price', fontsize = 16, labelpad = 10)
            im.plot(df['date'],df['price'], "ro")
            fig.subplots_adjust(bottom=0.2)
            #convert to png
            pngim = io.BytesIO()
            FigureCanvas(fig).print_png(pngim)
            #convert to 64-bit string
            pngim64 = "data:image/png;base64,"
            pngim64 += base64.b64encode(pngim.getvalue()).decode('utf8')
            #serve up plot and link back to landing page
            return render_template("image.html", image=pngim64, value=tickersym)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
