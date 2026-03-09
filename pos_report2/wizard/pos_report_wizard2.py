from odoo import fields, models


class PosReportWizard2(models.TransientModel):
    _name = "pos.report2.wizard"
    _description='pos report wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    company_id = fields.Many2one('res.company', string='Regions', required=True)
    branch_ids = fields.Many2many('res.branch', string="branches")

    def print_report_2(self):
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'company_id': self.company_id.id,
            'branch_ids': self.branch_ids.ids
        }
        return self.env.ref('pos_report2.pos_report2').report_action(self, data=data, config=False)


class PosReport2(models.AbstractModel):
    _name = 'report.pos_report2.pos_report_2'
    _inherit = 'report.report_xlsx.abstract'
    _description='report 2'

    def generate_xlsx_report(self, workbook, data, objs):
        start_date = data['from_date']
        end_date = data['to_date']
        company_id = data['company_id']
        branch_ids = data['branch_ids']
        domain = [('start_at', '>=', start_date), ('start_at', '<=', end_date)]
        if company_id:
            domain += [('company_id', '=', company_id)]
        if branch_ids:
            domain += [('branch_id', 'in', branch_ids)]
        pos_payment = self.env['pos.session'].search(domain)
        payment_method_names = pos_payment.mapped('payment_method_ids.name')
        payment_names = list(set(payment_method_names))
        payment_names.sort()

        # design of the report
        format1 = workbook.add_format(
            {'font_size': 12, 'bg_color': '#2e90db', 'color': 'white', 'bold': True, 'text_wrap': True})
        format2 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})

        # report header
        sheet = workbook.add_worksheet("Sales Closing Report")
        sheet.write(1, 3, '[' + data['from_date'] + ' to ' + data['to_date'] + ']', format2)
        sheet.write(2, 0, 'Sales Chanel', format1)
        sheet.write(2, 1, 'Branch', format1)
        sheet.write(2, 2, 'Date', format1)
        count = 3
        for name in payment_names:
            sheet.write(2, count, name, format1)
            count += 1
        sheet.write(2, count, 'Total paid sales', format1)
        sheet.write(2, count + 1, 'Total sales include VAT', format1)
        sheet.write(2, count + 2, 'unpaid invoice', format1)
        sheet.write(2, count + 3, 'opening cash', format1)
        sheet.write(2, count + 4, 'Credit Cards Deposits', format1)
        sheet.write(2, count + 5, 'Cash deposits', format1)
        sheet.write(2, count + 6, 'Miscellaneous cash out', format1)
        sheet.write(2, count + 7, 'Gift Invoice', format1)
        sheet.write(2, count + 8, 'closing cash', format1)

        r = 3
        for rec in pos_payment:
            sheet.write(r, 0, rec.branch_id.name)
            sheet.write(r, 1, rec.branch_id.name)
            sheet.write(r, 2, str(rec.start_at.date()))
            col = 3
            total_card_amount = 0
            if rec.id:
                for p_name in payment_names:
                    self.env.cr.execute("""
                                    SELECT ppm.name as p_name,sum(amount) as amount,ppm.is_cash_count as is_cash
                                    FROM pos_payment as pp,pos_payment_method as ppm 
                                    WHERE session_id=%(rec_id)s and ppm.name::text = %(payment_name)s 
                                    and ppm.id = pp.payment_method_id 
                                    GROUP BY ppm.name,ppm.is_cash_count ORDER BY ppm.name
                                    """, {'rec_id': rec.id, 'payment_name': p_name})
                    payments = self.env.cr.dictfetchall()
                    if payments:
                        for payment in payments:
                            amount = payment.get('amount')
                            sheet.write(r, col, amount)
                            is_cash = payment.get('is_cash')
                            if not is_cash:
                                total_card_amount += amount
                            col += 1
                    else:
                        sheet.write(r, col, 0)
                        col += 1
            else:
                payments = []
            sheet.write(r, col, rec.total_payments_amount)
            sheet.write(r, col + 1, rec.total_payments_amount)
            sheet.write(r, col + 2, 0)
            balance_start = balance_end_real = cash_out = cash_in = 0
            
            balance_start = rec.cash_register_balance_start or 0
            balance_end_real = rec.cash_register_balance_end_real or 0
            
            if rec.move_id:
                for line in rec.move_id.line_ids:
                    if line.account_id.account_type == 'asset_cash':
                        if line.balance > 0:
                            cash_in += line.balance
                        elif line.balance < 0:
                            cash_out += abs(line.balance)
            
            sheet.write(r, col + 3, balance_start)
            sheet.write(r, col + 4, total_card_amount)
            sheet.write(r, col + 5, abs(cash_in))
            sheet.write(r, col + 6, cash_out)
            total_gifts_amount = 0
            if rec.order_ids:
                for order in rec.order_ids:
                    # Check all loyalty cards (gift cards) used in this order
                    for line in order.lines:
                        if line.coupon_id and line.coupon_id.program_type == 'gift_card':
                            # For gift cards, we want the amount used (negative for redemption)
                            if line.price_subtotal_incl < 0:  # Redemption (using gift card)
                                total_gifts_amount += abs(line.price_subtotal_incl)
                            elif line.price_subtotal_incl > 0:  # Purchase (buying gift card)
                                total_gifts_amount += line.price_subtotal_incl
            sheet.write(r, col + 7, abs(total_gifts_amount))
            sheet.write(r, col + 8, balance_end_real)

            r += 1