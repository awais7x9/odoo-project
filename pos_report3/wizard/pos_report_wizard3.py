from odoo import fields, models
import datetime


class PosReportWizard3(models.TransientModel):
    _name = "pos.report3.wizard"
    _description='report 3 wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    company_id = fields.Many2one('res.company', string='Regions', required=True)
    branch_id = fields.Many2many('res.branch', string="branches")
    return_ref = fields.Char(string="Return TRX number")

    def print_report_1(self):
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'company_id': self.company_id.id,
            'branch_id': self.branch_id.ids,
            'return_ref': self.return_ref,
        }
        return self.env.ref('pos_report3.pos_report3').report_action(self, data=data, config=False)


class PosReport3(models.AbstractModel):
    _name = 'report.pos_report3.pos_report_3'
    _inherit = 'report.report_xlsx.abstract'
    _description ='report 3 wiz'

    def generate_xlsx_report(self, workbook, data, objs):
        domain = [('refunded_orderline_id', '!=', False), ('full_product_name', 'not ilike', 'discount')]

        start_date = data['from_date']
        end_date = data['to_date']
        company_id = data['company_id']
        branch_id = data['branch_id']
        return_ref = data['return_ref']

        if start_date:
            domain += [('create_date', '>=', start_date)]
        if end_date:
            domain += [('create_date', '<=', end_date)]
        if company_id:
            domain += [('company_id', '=', company_id)]
        if branch_id:
            domain += [('branch_id', 'in', branch_id)]
        if return_ref:
            return_order_ref = self.env['pos.order'].search([('pos_reference', '=', return_ref)], limit=1).id
            domain += [('order_id', '=', return_order_ref)]
        return_order = self.env['pos.order.line'].search(domain)

        # design of the report
        format1 = workbook.add_format({'font_size': 12, 'bg_color': '#2e90db', 'color': 'white', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})
        format3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})

        # report header
        report_name = 'Sales Return Report'
        sheet = workbook.add_worksheet(report_name)
        # sheet.merge_range(static_row, static_col, static_row, col_merge, "Date range", heading_format)
        # sheet.set_column(4, 1, 25)
        # sheet.set_column(4, 2, 30)
        # sheet.set_column(4, 3, 30)
        # sheet.set_column(4, 4, 20)
        # sheet.set_column(4, 5, 20)
        # sheet.set_column(4, 6, 20)

        sheet.merge_range(2, 1, 2, 12, report_name, format3)
        sheet.merge_range(5, 1, 5, 12, '[' + data['from_date'] + ' to ' + data['to_date'] + ']', format2)
        # sheet.write(2, 3, report_name, format3)
        # sheet.write(3, 1, "", format2)
        # sheet.write(3, 2, "", format2)
        # sheet.write(3, 4, "", format2)
        # sheet.write(3, 5, "", format2)
        # sheet.write(3, 6, "", format2)
        # sheet.write(5, 1, "", format2)
        # sheet.write(5, 2, "", format2)
        # sheet.write(5, 4, "", format2)
        # sheet.write(5, 5, "", format2)
        # sheet.write(5, 6, "", format2)
        # sheet.write(5, 3, , format2)

        # # header of the table her
        sheet.write(7, 1, 'Outlet Name', format1)
        sheet.write(7, 2, 'DATE', format1)
        sheet.write(7, 3, 'Return TRX. No', format1)
        sheet.write(7, 4, 'SKU', format1)
        sheet.write(7, 5, 'Item Discerptions', format1)
        sheet.write(7, 6, 'Return QTY', format1)
        sheet.write(7, 7, 'Total( Day ) Sales include VAT Without return/item', format1)
        sheet.write(7, 8, 'RTN amount included Vat', format1)
        sheet.write(7, 9, 'Net ( Day ) sales include VAT Without return/item', format1)
        sheet.write(7, 10, 'Orginal Sales Invoice no. Related to TRN', format1)
        sheet.write(7, 11, 'Orginal Sales Invoice Date', format1)
        sheet.write(7, 12, 'Orginal Sales Invoice amount incl. VAT', format1)

        j = 7
        for rec in return_order:
            j = j + 1
            sheet.write(j, 1, rec.branch_id.name)
            sheet.write(j, 2, str(rec.create_date.date()))
            sheet.write(j, 3, rec.order_id.pos_reference)
            sheet.write(j, 4, rec.product_id.barcode)
            sheet.write(j, 5, rec.product_id.name)
            sheet.write(j, 6, abs(rec.qty))
            # need total day wise sale
            s_date = datetime.datetime.strptime(str(rec.create_date.date()), '%Y-%m-%d')
            c_end_date = s_date.replace(hour=23, minute=59, second=59)
            self.env.cr.execute("""
                                select sum(pol.price_subtotal_incl) as total
                                from pos_order_line as pol
                                where pol.product_id = %(product_id)s and pol.branch_id = %(branch_id)s and
                                pol.create_date >= %(s_date)s and pol.create_date <= %(c_end_date)s and
                                pol.refunded_orderline_id is null
                                    """, {'s_date': s_date,
                                          'c_end_date': c_end_date,
                                          'product_id': rec.product_id.id,
                                          'branch_id': rec.branch_id.id})
            current_day_sale_product = self.env.cr.dictfetchall()
            total_product_sale = 0
            if current_day_sale_product[0]['total'] is not None:
                total_product_sale = current_day_sale_product[0]['total']
            sheet.write(j, 7, total_product_sale)
            sheet.write(j, 8, rec.price_subtotal_incl)
            sheet.write(j, 9, (total_product_sale - abs(rec.price_subtotal_incl)))
            sheet.write(j, 10, rec.order_id.refunded_order_id.pos_reference)
            sheet.write(j, 11, str(rec.order_id.refunded_order_id.date_order.date()))
            sheet.write(j, 12, rec.order_id.refunded_order_id.amount_total)
