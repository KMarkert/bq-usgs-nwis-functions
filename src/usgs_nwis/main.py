import json
import logging
import pandas as pd
import dataretrieval.nwis as nwis

import functions_framework


@functions_framework.http
def get_streamflow(request):
    try:
      request_json = request.get_json(silent=True)
      calls = request_json['calls']

      # unpack the call data
      stations, dates = list(zip(*calls))

      # get the first station from call
      # this assumes that all rows have the same station
      station = stations[0]

      # extract the min and max date range for the call
      # don't want to loop through all dates but make one call to nwis
      min_date, max_date = min(dates), max(dates)
      print(min_date, max_date)
      
      # request the data from NWIS API for the time range
      # this is more efficient than looping through each
      gauge = nwis.get_record(
        sites=station, 
        service='dv', 
        start=min_date, 
        end=max_date, 
        parameterCd='00060'
      )
      
      # convert cfs to cms
      gauge['streamflow'] = gauge['00060_Mean'] * 0.02832

      # make sure to only get the data for the times requested
      # this insures the n rows are same for returned data
      gauge_req = gauge.loc[gauge.index.strftime('%Y-%m-%d').isin(dates)]

      # convert to list to pass to the response
      replies = gauge_req['streamflow'].tolist()

      return json.dumps({'replies': replies})

    except Exception as e:
      
      return json.dumps({ "errorMessage": str(e) }), 400