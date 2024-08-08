#!/usr/bin/env` python3
# -*- coding: utf-8 -*-

from csv import DictWriter
from glob import glob
from ofxparse import OfxParser
import json
import urllib.request
import datetime
import argparse
import regex as re

argparser = argparse.ArgumentParser()
argparser.add_argument("-o", "--outputtype", help = "csv or json", default="csv")
argparser.add_argument("-i", "--input", nargs='+', help = "input file(s)", default="*.ofx")
args = argparser.parse_args()

DATE_FORMAT = "%m/%d/%Y"
jsonBody = {}
outputtype = args.outputtype
jsonBody["data"] = []
allStatements = []


def write_csv(statement, out_file):
    print("Writing: " + out_file)
    fields = ['Date', 'Description (payee)', 'Transaction Type (type)', 'UID', 'Amount',
              'sic', 'mcc', 'Notes (memo)', 'Debit', 'Credit', 'Balance', 'FID', 'Organization']
    with open(out_file, 'w', newline='') as f:
        writer = DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for line in statement:
            writer.writerow(line)


def get_statement_from_qfx(qfx):
    balance = qfx.account.statement.balance
    statement = []
    credit_transactions = ['credit', 'dep', 'int', 'directdep']
    debit_transactions = ['debit', 'atm', 'pos',
                          'xfer', 'check', 'fee', 'payment']
    other_transactions = ['other']
    for transaction in qfx.account.statement.transactions:
        credit = ""
        debit = ""
        balance = balance + transaction.amount
        if transaction.type in credit_transactions:
            credit = transaction.amount
        elif transaction.type in debit_transactions:
            debit = -transaction.amount
        elif transaction.type in other_transactions:
            if transaction.amount < 0:
                debit = -transaction.amount
            else:
                credit = transaction.amount
        else:
            raise ValueError("Unknown transaction type:" + transaction.type)

        line = {
            'Date': transaction.date.strftime(DATE_FORMAT),
            'Description (payee)': transaction.payee,
            'Transaction Type (type)': transaction.type,
            'Notes (memo)': transaction.memo,
            'UID': transaction.id,
            'Amount': str(transaction.amount),
            'sic': transaction.sic,
            'mcc': transaction.mcc,
            'Debit': str(debit),
            'Credit': str(credit),
            'Balance': str(balance),
            'FID': qfx.account.institution.fid,
            'Organization': qfx.account.institution.organization}
        statement.append(line)
        jsonBody["data"].append(line)
    return statement

files = args.input
for qfx_file in files:
    qfx = OfxParser.parse(open(qfx_file, encoding="utf8", errors="ignore"))
    statement = get_statement_from_qfx(qfx)
    allStatements = allStatements + statement
    if outputtype == 'csv':
        out_file = "converted_" + re.sub('(.*\\\+|\/+)', '', qfx_file.replace(".ofx", ".csv"))
        write_csv(allStatements, out_file)
    elif outputtype == 'json' and (len(args.input) > 1 or args.input == '*.ofx'):
        print('json output supports one file only')
    else:
        with open('qfx-transactions.json', 'w') as outfile:
            json.dump(jsonBody, outfile)