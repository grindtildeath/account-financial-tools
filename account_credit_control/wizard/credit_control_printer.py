# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64

from openerp import models, fields, api, _


class CreditControlPrinter(models.TransientModel):
    """ Print lines """

    _name = "credit.control.printer"
    _rec_name = 'id'
    _description = 'Mass printer'

    @api.model
    def _get_line_ids(self):
        context = self.env.context
        if context.get('active_model') != 'credit.control.line':
            return False
        return context.get('active_ids', False)

    mark_as_sent = fields.Boolean(string='Mark letter lines as sent',
                                  default=True,
                                  help="Only letter lines will be marked.")
    report_file = fields.Binary(string='Generated Report', readonly=True)
    report_name = fields.Char(string='Report name')
    state = fields.Char(string='state')
    line_ids = fields.Many2many('credit.control.line',
                                string='Credit Control Lines',
                                default=_get_line_ids)

    @api.model
    def _credit_line_predicate(self, line):
        return True

    @api.model
    @api.returns('credit.control.line')
    def _get_lines(self, lines, predicate):
        return lines.filtered(predicate)

    @api.multi
    def print_lines(self):
        self.ensure_one()
        comm_obj = self.env['credit.control.communication']
        if not self.line_ids and not self.print_all:
            raise api.Warning(_('No credit control lines selected.'))

        lines = self._get_lines(self.line_ids, self._credit_line_predicate)

        comms = comm_obj._generate_comm_from_credit_lines(lines)

        report_content = comms._generate_report()

        self.write({'report_file': base64.b64encode(report_content),
                    'report_name': ('credit_control_esr_bvr_%s.pdf' %
                                    fields.datetime.now()),
                    'state': 'done'})

        if self.mark_as_sent:
            comms._mark_credit_line_as_sent()
        action = self.get_formview_action()[0]
        action['target'] = 'new'
        return action
