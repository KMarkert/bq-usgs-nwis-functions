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
      n_calls = len(calls)

      # unpack the call data
      stations, dates = list(zip(*calls))

      # get the unique stations in call
      stations_set = list(set(stations))

      # extract the min and max date range for the call
      # don't want to loop through all dates but make one call to nwis
      min_date, max_date = min(dates), max(dates)
      print(f'Station set: {stations_set}\nMin date: {min_date}\nMax date: {max_date}')
      
      # request the data from NWIS API for the time range
      # and multiple stations if in call
      # this is more efficient than looping through each
      gauge = nwis.get_record(
        sites=stations_set, 
        service='dv', 
        start=min_date, 
        end=max_date, 
        parameterCd='00060'
      )
      
      # convert cfs to cms
      gauge['streamflow'] = gauge['00060_Mean'] * 0.02832

      if len(stations_set) > 1:
        # if there are multiple stations in the call
        # get the station and dates index for selecting data
        ix = pd.MultiIndex.from_arrays(
          [stations, dates], 
          names = ('site_no','datetime')
        )

      else:
        # if only one station
        # get the dates index for selecting data
        ix = dates

      # check if there is too little or too much data returned by NWIS
      if n_calls > gauge.shape[0]:
          gauge_req = gauge.reindex(ix)
      elif n_calls < gauge.shape[0]:
        gauge_req = gauge.loc[ix]
      else:
        gauge_req = gauge

      # convert to list to pass to the response
      # and set poor data to -999999 value
      replies = gauge_req['streamflow'].where(
        gauge_req['streamflow']>=0, -999999
      ).fillna(-999999).tolist()

      return json.dumps({'replies': replies})

    except Exception as e:
      
      return json.dumps({ "errorMessage": str(e) }), 400