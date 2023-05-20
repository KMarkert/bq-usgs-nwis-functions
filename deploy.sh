#!/bin/bash

#####################################################################################################
# Script Name: deploy.sh
# Date of Creation: 2023-05-20
# Author: Kel Markert
# 
# Modified from https://github.com/dojowahi/earth-engine-on-bigquery/blob/main/deploy_cf.sh
#####################################################################################################

source ./config.sh

CF_NWIS="usgs-nwis"

echo "Deploying NWIS CF..."

cd src/usgs_nwis

#Deploy the cloud function
gcloud functions deploy ${CF_NWIS} --entry-point get_streamflow --runtime python39 --trigger-http --allow-unauthenticated --project ${PROJECT_ID} --gen2 --region ${REGION} --memory 256MB

#Add Cloud Invoker function role

echo "Cloud function successfully deployed!"

echo "Checking endpoint..."

ENDPOINT=$(gcloud functions describe ${CF_NWIS} --gen2 --region=${REGION} --format=json | jq -r '.serviceConfig.uri')

echo "${CF_NWIS} endpoint found at ${ENDPOINT}!"

echo "Creating BQ function connection..."

#Create the external connection for BQ
bq mk --connection --display_name='my_rf_nwis_conn' \
      --connection_type=CLOUD_RESOURCE \
      --project_id=${PROJECT_ID} \
      --location=US  rf-nwis-conn

#Create table with remote function call
bq mk -d usgs_nwis

# create the remote function for the table
build_sql="CREATE OR REPLACE FUNCTION usgs_nwis.get_streamflow(site STRING, time DATE) RETURNS FLOAT64 REMOTE WITH CONNECTION \`${PROJECT_ID}.us.rf-nwis-conn\` OPTIONS ( endpoint = '${ENDPOINT}')"

bq query --use_legacy_sql=false ${build_sql}

echo "Done!"