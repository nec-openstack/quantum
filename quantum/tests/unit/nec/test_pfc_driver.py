# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2012 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
# @author: Ryota MIBU

import random
import string

import mox
import unittest

from quantum.common import utils
from quantum.openstack.common import uuidutils
from quantum.plugins.nec import drivers
from quantum.plugins.nec.db import models as nmodels
from quantum.plugins.nec.common import ofc_client as ofc


class TestConfig(object):
    """Configuration for this test"""
    host = '127.0.0.1'
    port = 8888
    use_ssl = False
    key_file = None
    cert_file = None


def _ofc(val):
    """OFC ID converter (shrink UUID to unique 31-char string)"""
    vals = val.split('-')
    vals[2] = vals[2][1:]
    return ''.join(vals)


def _ofc_desc(val):
    """OFC description converter (replace hyphen and space to underscore)"""
    return val.replace('-', '_').replace(' ', '_')[:127]


class PFCDriverTestBase(unittest.TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.driver = drivers.get_driver("pfc")(TestConfig)
        self.mox.StubOutWithMock(ofc.OFCClient, 'do_request')

    def tearDown(self):
        self.mox.UnsetStubs()

    def get_ofc_item_random_params(self):
        """create random parameters for ofc_item test"""
        tenant_id = utils.str_uuid()
        network_id = utils.str_uuid()
        port_id = utils.str_uuid()
        portinfo = nmodels.PortInfo(id=port_id, datapath_id="0x123456789",
                                    port_no=1234, vlan_id=321,
                                    mac="11:22:33:44:55:66")
        return tenant_id, network_id, portinfo

    def testa_create_tenant(self):
        t, n, p = self.get_ofc_item_random_params()
        description = "desc of %s" % t

        path = "/tenants"
        body = {'id': _ofc(t)}
        tenant = {}
        ofc.OFCClient.do_request("POST", path, body=body).AndReturn(tenant)
        self.mox.ReplayAll()

        ret = self.driver.create_tenant(description, t)
        self.mox.VerifyAll()
        self.assertEqual(ret, _ofc(t))

    def testb_update_tenant(self):
        t, n, p = self.get_ofc_item_random_params()
        description = "new desc of %s" % t

        path = "/tenants/%s" % _ofc(t)
        body = {'description': _ofc_desc(description)}
        ofc.OFCClient.do_request("PUT", path, body=body)
        self.mox.ReplayAll()

        self.driver.update_tenant(_ofc(t), description)
        self.mox.VerifyAll()

    def testc_delete_tenant(self):
        t, n, p = self.get_ofc_item_random_params()

        path = "/tenants/%s" % _ofc(t)
        ofc.OFCClient.do_request("DELETE", path)
        self.mox.ReplayAll()

        self.driver.delete_tenant(_ofc(t))
        self.mox.VerifyAll()

    def testd_create_network(self):
        t, n, p = self.get_ofc_item_random_params()
        description = "desc of %s" % n

        path = "/tenants/%s/networks" % _ofc(t)
        body = {'id': _ofc(n), 'description': _ofc_desc(description)}
        network = {}
        ofc.OFCClient.do_request("POST", path, body=body).AndReturn(network)
        self.mox.ReplayAll()

        ret = self.driver.create_network(_ofc(t), description, n)
        self.mox.VerifyAll()
        self.assertEqual(ret, _ofc(n))

    def teste_update_network(self):
        t, n, p = self.get_ofc_item_random_params()
        description = "desc of %s" % n

        path = "/tenants/%s/networks/%s" % (_ofc(t), _ofc(n))
        body = {'description': _ofc_desc(description)}
        ofc.OFCClient.do_request("PUT", path, body=body)
        self.mox.ReplayAll()

        self.driver.update_network(_ofc(t), _ofc(n), description)
        self.mox.VerifyAll()

    def testf_delete_network(self):
        t, n, p = self.get_ofc_item_random_params()

        path = "/tenants/%s/networks/%s" % (_ofc(t), _ofc(n))
        ofc.OFCClient.do_request("DELETE", path)
        self.mox.ReplayAll()

        self.driver.delete_network(_ofc(t), _ofc(n))
        self.mox.VerifyAll()

    def testg_create_port(self):
        t, n, p = self.get_ofc_item_random_params()

        path = "/tenants/%s/networks/%s/ports" % (_ofc(t), _ofc(n))
        body = {'id': _ofc(p.id),
                'datapath_id': p.datapath_id,
                'port': str(p.port_no),
                'vid': str(p.vlan_id)}
        port = {}
        ofc.OFCClient.do_request("POST", path, body=body).AndReturn(port)
        self.mox.ReplayAll()

        ret = self.driver.create_port(_ofc(t), _ofc(n), p, p.id)
        self.mox.VerifyAll()
        self.assertEqual(ret, _ofc(p.id))

    def testh_delete_port(self):
        t, n, p = self.get_ofc_item_random_params()

        path = "/tenants/%s/networks/%s/ports/%s" % (_ofc(t), _ofc(n),
                                                     _ofc(p.id))
        ofc.OFCClient.do_request("DELETE", path)
        self.mox.ReplayAll()

        self.driver.delete_port(_ofc(t), _ofc(n), _ofc(p.id))
        self.mox.VerifyAll()


class PFCDriverStringTest(unittest.TestCase):

    driver = 'quantum.plugins.nec.drivers.pfc.PFCDriverBase'

    def setUp(self):
        super(PFCDriverStringTest, self).setUp()
        self.driver = drivers.get_driver("pfc")(TestConfig)

    def test_generate_pfc_id_uuid(self):
        id_str = uuidutils.generate_uuid()
        exp_str = (id_str[:14] + id_str[15:]).replace('-', '')[:31]

        ret_str = self.driver._generate_pfc_id(id_str)
        self.assertEqual(exp_str, ret_str)

    def test_generate_pfc_id_uuid_no_hyphen(self):
        # Keystone tenant_id style uuid
        id_str = uuidutils.generate_uuid()
        id_no_hyphen = id_str.replace('-', '')
        exp_str = (id_str[:14] + id_str[15:]).replace('-', '')[:31]

        ret_str = self.driver._generate_pfc_id(id_no_hyphen)
        self.assertEqual(exp_str, ret_str)

    def test_generate_pfc_id_string(self):
        id_str = uuidutils.generate_uuid() + 'x'
        exp_str = id_str[:31].replace('-', '_')

        ret_str = self.driver._generate_pfc_id(id_str)
        self.assertEqual(exp_str, ret_str)

    def test_generate_pfc_desc(self):
        random_list = [random.choice(string.printable) for x in range(128)]
        random_str = ''.join(random_list)

        accept_letters = string.letters + string.digits
        exp_list = [x if x in accept_letters else '_' for x in random_list]
        exp_str = ''.join(exp_list)[:127]

        ret_str = self.driver._generate_pfc_description(random_str)
        self.assertEqual(exp_str, ret_str)
