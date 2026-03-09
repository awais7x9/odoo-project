# -*- coding: utf-8 -*-
{
    'name': "Sales Closing Report",
    'version': '18.0.0.0.1',
    'category': 'Customizations',
    'summary': """
        Sales Closing Report
        """,

    'description': """
        This module is used for POS XLSX report2(IBQ)
    """,

    'author': "AMB",
    'website': "telenoc.org",

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'report_xlsx', 'account', 'bi_branch_pos', 'pos_loyalty'],

    # always loaded
    'data': [
        'report/pos_order_print.xml',
        'wizard/pos_report_2.xml',
        'security/ir.model.access.csv',
    ],

}
