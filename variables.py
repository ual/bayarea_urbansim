import numpy as np
import pandas as pd
from urbansim.utils import misc
import urbansim.sim.simulation as sim
import datasources
from urbansim_defaults import utils
from urbansim_defaults import variables


#####################
# COSTAR VARIABLES
#####################


@sim.column('costar', 'general_type')
def general_type(costar):
    return costar.PropertyType


@sim.column('costar', 'rent')
def rent(costar):
    return costar.averageweightedrent


@sim.column('costar', 'stories')
def stories(costar):
    return costar.number_of_stories


@sim.column('costar', 'node_id')
def node_id(parcels, costar):
    return misc.reindex(parcels.node_id, costar.parcel_id)


@sim.column('costar', 'zone_id')
def node_id(parcels, costar):
    return misc.reindex(parcels.zone_id, costar.parcel_id)


#####################
# JOBS VARIABLES
#####################


@sim.column('jobs', 'naics', cache=True)
def naics(jobs):
    return jobs.naics11cat


@sim.column('jobs', 'empsix', cache=True)
def empsix(jobs, naics_to_empsix):
    return jobs.naics.map(naics_to_empsix)


@sim.column('jobs', 'empsix_id', cache=True)
def empsix_id(jobs, empsix_name_to_id):
    return jobs.empsix.map(empsix_name_to_id)


#####################
# HOMESALES VARIABLES
#####################


@sim.column('homesales', 'sale_price_flt')
def sale_price_flt(homesales):
    col = homesales.Sale_price.str.replace('$', '').\
        str.replace(',', '').astype('f4') / homesales.sqft_per_unit
    col[homesales.sqft_per_unit == 0] = 0
    return col


@sim.column('homesales', 'year_built')
def year_built(homesales):
    return homesales.Year_built


@sim.column('homesales', 'lot_size_per_unit')
def lot_size_per_unit(homesales):
    return homesales.Lot_size


@sim.column('homesales', 'sqft_per_unit')
def sqft_per_unit(homesales):
    return homesales.SQft


@sim.column('homesales', 'city')
def city(homesales):
    return homesales.City


@sim.column('homesales', 'zone_id')
def zone_id(parcels, homesales):
    return misc.reindex(parcels.zone_id, homesales.parcel_id)


@sim.column('homesales', 'node_id')
def node_id(parcels, homesales):
    return misc.reindex(parcels.node_id, homesales.parcel_id)


#####################
# PARCELS VARIABLES
#####################


def parcel_average_price(use, quantile=.5):
    # I'm testing out a zone aggregation rather than a network aggregation
    # because I want to be able to determine the quantile of the distribution
    # I also want more spreading in the development and not keep it so localized
    if use == "residential":
        buildings = sim.get_table('buildings')
        return misc.reindex(buildings.
                            residential_sales_price[buildings.general_type ==
                                                    "Residential"].
                            groupby(buildings.zone_id).quantile(quantile),
                            sim.get_table('parcels').zone_id)
    return misc.reindex(sim.get_table('nodes_prices')[use],
                        sim.get_table('parcels').node_id)


def parcel_sales_price_sqft(use):
    return parcel_average_price(use, .8)


def parcel_is_allowed(form):
    form_to_btype = sim.get_injectable("form_to_btype")
    # we have zoning by building type but want
    # to know if specific forms are allowed
    allowed = [sim.get_table('zoning_baseline')
               ['type%d' % typ] == 't' for typ in form_to_btype[form]]
    return pd.concat(allowed, axis=1).max(axis=1).\
        reindex(sim.get_table('parcels').index).fillna(False)


@sim.column('parcels', 'max_far', cache=True)
def max_far(parcels, scenario):
    return utils.conditional_upzone(scenario, "max_far", "far_up").\
        reindex(parcels.index).fillna(0)


@sim.column('parcels', 'max_dua', cache=True)
def max_dua(parcels, scenario):
    return utils.conditional_upzone(scenario, "max_dua", "dua_up").\
        reindex(parcels.index).fillna(0)


@sim.column('parcels', 'max_height', cache=True)
def max_height(parcels, zoning_baseline):
    return zoning_baseline.max_height.reindex(parcels.index).fillna(0)


# for debugging reasons this is split out into its own function
@sim.column('parcels', 'building_purchase_price_sqft')
def building_purchase_price_sqft():
    return parcel_average_price("residential", .6)


@sim.column('parcels', 'building_purchase_price')
def building_purchase_price(parcels, nodes_prices):
    if len(nodes_prices) == 0:
        # if nodes_prices isn't generated yet
        return pd.Series(index=parcels.index)

    return (parcels.total_sqft * parcels.building_purchase_price_sqft).\
        reindex(parcels.index).fillna(0)


@sim.column('parcels', 'land_cost')
def land_cost(parcels, nodes_prices):
    if len(nodes_prices) == 0:
        # if nodes_prices isn't generated yet
        return pd.Series(index=parcels.index)

    return parcels.building_purchase_price + parcels.parcel_size * 20.0


@sim.column('parcels', 'node_id')
def node_id(parcels):
    return parcels._node_id