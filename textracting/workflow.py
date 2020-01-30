# download reports from s3 gsq-staging ?

# run textracting on reports, saving various json, csv, txt files

# with small number of noisy reports, remove noise with heuristics, (and potentially use dataset and model in the future)
    # cleanpage s are created from pagelineinfo. from these, restructpagelines are be created

# create toc dataset from files and train
# todo create figure dataset and train figure page classifier

# todo create heading recognition dataset and train
# todo create heading identification dataset and train


import textmain
import textloading
import search_report
import texttransforming
from heading_id_intext import Text2CNBPrediction, Num2Cyfra1, num2cyfra1  # have to load these to load the model
import os
import settings
import pandas as pd
import time
import csv
import datetime
import argparse
import numpy as np
import warnings


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument("--id", help="report ID to bookmark", type=str)
    parser.add_argument("--id", help="report IDs to bookmark", nargs='+')  # list type
    parser.add_argument("-s", "--sample", help='number of reports to sample', type=int)
    parser.add_argument("-c", "--cutoffdate", help="cutoff year for reports to be no older than", type=int)
    parser.add_argument("-e", "--exclude", help="report types to exclude. must match report type code eg. WELCOM for Well Completion Report")
    args = parser.parse_args()
    mode = 'sample'  # default behaviour is random sampling
    if args:
        warnings.filterwarnings("ignore")
    if args.sample:
        mode = 'sample'
        num_sample = args.sample
        if args.cutoffdate:
            cutoffdate = pd.Timestamp(args.cutoffdate, 1, 1)
        else: cutoffdate = None
        if args.exclude:
            rtype_exclude = args.exclude
        else: rtype_exclude = None

    if args.id:
        docids = args.id
        mode = 'given'

    if mode == 'sample':
        if not args.sample:
            num_sample = 20
            cutoffdate = None
            rtype_exclude = 'WELCOM'
        print("Running in sample mode. Num samples: " + str(num_sample) + " Cutoff date: " + str(cutoffdate) +
              " Excluding: " + str(rtype_exclude))

        docids = textloading.get_reportid_sample(num=num_sample, cutoffdate=cutoffdate, rtype_exclude=rtype_exclude)
    else:
        print("Running in 'given' mode")

    training_folders = os.walk('training/QDEX/')
    training_docids = [x[0].split('\\')[-1] for x in training_folders]
    #docids = ['15042', '41275', '4639', '48670', '593', '3051', '24357', '15568', '68677', '48897', '36490', '5261', '44433'] #'41568', '41982', '10189', '102109', '43758', '105472', '48907'
    print("Report IDs to bookmark: ",  docids)

    log_file = 'bookmarker_log.csv'
    # log file cols = report_id, time2textract, time2ml, toc, time_run
    if not os.path.exists(log_file):
        with open(log_file, "w", newline='') as log:
            writer = csv.writer(log)
            writer.writerow(['report_id', 'time2textract', 'time2ml', 'toc', 'time_run'])

    for docid in docids:
        #if docid not in training_docids:
            # all the below checks also need to check if the --force arg is True, which would overrule their skip
            # check if textract needs to be run or if fulljson already exists
            textract_start = time.time()
            try:
                textmain.textract(docid, features=['TABLES', 'FORMS'])
            except FileNotFoundError:
                print("Report file doesn't exist in S3")
                continue
            textract_end = time.time()
            textract_time = textract_end - textract_start
            print("Time to textract: " + str(docid) + " " + "{0:.2f}".format(textract_time) + " seconds")
            ml_start = time.time()
            # check if clean and restruct needs to be run or if restructpageinfo alredy exists
            texttransforming.clean_and_restruct(docid)
            # check if search report, bookmark report, needs to be run or if bookmarked pdf already exists
            report = search_report.Report(docid)  # need every ml method here to be able to create a dataset with an unseen report
            #search_report.draw_report(report)
            search_report.bookmark_report(report)
            # check if needs to be run or if sections word doc already exists
            search_report.save_report_sections(report)
            ml_end = time.time()
            ml_time = ml_end - ml_start
            print("Time to ML, bookmark, export to text: " + "{0:.2f}".format(ml_time) + " seconds")
            print("COMPLETED BOOKMARKING " + docid + ", total time: " + "{0:.2f}".format(ml_time + textract_time) + " seconds")
            toc_exists = True if report.toc_page else False
            bookmark_time = datetime.datetime.now()
            with open(log_file, 'a', newline='') as log:
                writer = csv.writer(log)
                writer.writerow([int(docid), textract_time, ml_time, toc_exists, bookmark_time])
