#! /usr/bin/env python
"""
Version of Services/PhEDEx intended to be used with mock or unittest.mock
"""

from __future__ import (division, print_function)

import json
import os

from RestClient.ErrorHandling.RestClientExceptions import HTTPError
from WMCore.WMBase import getTestBase


NOT_EXIST_DATASET = 'thisdoesntexist'
PILEUP_DATASET = '/HighPileUp/Run2011A-v1/RAW'

SITES = ['T2_XX_SiteA', 'T2_XX_SiteB', 'T2_XX_SiteC']
_BLOCK_LOCATIONS = {}

mockData = {}

# Read in the data just once so that we don't have to do it for every test (in __init__)
#TODO: this needs to be change to PhEDEx mock file
#globalFile = os.path.join(getTestBase(), '..', 'data', 'Mock', 'DBSMockData.json')

#try:
#    with open(globalFile, 'r') as mockFile:
#        mockData = json.load(mockFile)
#except IOError:
#    mockData = {}
    
class MockPhEDExApi(object):
    """
    Version of Services/PhEDEx intended to be used with mock or unittest.mock
    """

    def __init__(self, responseType="json"):
        pass

    def sitesByBlock(self, block):
        """
        Centralize the algorithm to decide where a block is based on the hash name

        Args:
            block: the name of the block

        Returns:
            sites: a fake list of sites where the data is

        """

        if hash(block) % 3 == 0:
            sites = ['T2_XX_SiteA']
        elif hash(block) % 3 == 1:
            sites = ['T2_XX_SiteA', 'T2_XX_SiteB']
        else:
            sites = ['T2_XX_SiteA', 'T2_XX_SiteB', 'T2_XX_SiteC']

        return sites

    def getReplicaPhEDExNodesForBlocks(self, block=None, dataset=None, complete='y'):
        """

        Args:
            block: the name of the block
            dataset: the name of the dataset
            complete: ??

        Returns:
            a fake list of blocks and the fakes sites they are at
        """

        if dataset:
            #TODO This is the real block name for PILEUP_DATASET - This should get it from the PhEDEx mock 
            return {'%s#0fcb2b12-d27e-11e0-91b1-003048caaace' % dataset: ['T2_XX_SiteA', 'T2_XX_SiteB', 'T2_XX_SiteC']}

        replicas = {}
        for oneBlock in block:
            if oneBlock.split('#')[0] == PILEUP_DATASET:
                # Pileup is at a single site
                sites = ['T2_XX_SiteC']
                _BLOCK_LOCATIONS[oneBlock] = sites
            else:
                sites = self.sitesByBlock(block=oneBlock)
                _BLOCK_LOCATIONS[oneBlock] = sites
            replicas.update({oneBlock: sites})
        return replicas

    def getReplicaInfoForBlocks(self, **args):
        """
        Where are blocks located
        """

        data = {"phedex": {"request_timestamp": 1254762796.13538, "block": []}}

        for block in args['block']:
            blocks = data['phedex']['block']
            # files = self.dataBlocks.getFiles(block)
            # locations = self.dataBlocks.getLocation(block)
            sites = self.sitesByBlock(block=block)
            blocks.append({'files': 1, 'name': block, 'replica': [{'node': x} for x in sites]})
        return data

    def getSubscriptionMapping(self, *dataItems, **kwargs):
        """
        Fake version of the existing PhEDEx method
        """

        dataItems = list(set(dataItems))  # force unique items
        locationMap = {}

        for dataItem in dataItems:
            sites = self.sitesByBlock(block=dataItem)
            locationMap.update({dataItem: sites})

        return locationMap

    def __getattr__(self, item):
        """
        __getattr__ gets called in case lookup of the actual method fails. We use this to return data based on
        a lookup table

        :param item: The method name the user is trying to call
        :return: The generic lookup function
        """

        def genericLookup(*args, **kwargs):
            """
            This function returns the mocked DBS data

            :param args: positional arguments it was called with
            :param kwargs: named arguments it was called with
            :return: the dictionary that DBS would have returned
            """

            if kwargs:
                signature = '%s:%s' % (item, sorted(kwargs.iteritems()))
            else:
                signature = item

            try:
                if mockData[self.url][signature] == 'Raises HTTPError':
                    raise HTTPError
                else:
                    return mockData[self.url][signature]
            except KeyError:
                raise KeyError("PhEDEx mock API could not return data for method %s, args=%s, and kwargs=%s (URL %s)." %
                               (item, args, kwargs, self.url))

        return genericLookup
