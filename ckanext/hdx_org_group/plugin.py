import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

import ckanext.hdx_org_group.actions.get as get_actions
import ckanext.hdx_org_group.actions.update as update_actions
import ckanext.hdx_org_group.actions.authorize as authorize
import ckanext.hdx_org_group.helpers.country_helper as country_helper
import ckanext.hdx_org_group.helpers.static_lists as static_lists

import ckanext.hdx_package.helpers.screenshot as screenshot

import ckanext.hdx_theme.helpers.custom_validator as custom_validator

from ckanext.hdx_org_group.helpers.analytics import OrganizationCreateAnalyticsSender

log = logging.getLogger(__name__)


group_type = 'country'


class HDXGroupPlugin(plugins.SingletonPlugin, lib_plugins.DefaultGroupForm):
    plugins.implements(plugins.IGroupForm, inherit=False)
    plugins.implements(plugins.IGroupController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)

    def group_types(self):
        return [group_type]

    def is_fallback(self):
        return True

    def _modify_group_schema(self, schema):
        schema.update({'language_code': [
            tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')], })
        schema.update({'relief_web_url': [
            tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]})
        schema.update({'hr_info_url': [
            tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]})
        schema.update({'geojson': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'custom_loc': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'customization': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'activity_level': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'featured_section': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'key_figures': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')],
                       'data_completeness': [tk.get_validator('ignore_missing'), tk.get_converter('convert_to_extras')]
                       })
        return schema

    def form_to_db_schema(self):
        schema = super(HDXGroupPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

    def db_to_form_schema(self):

        schema = super(HDXGroupPlugin, self).form_to_db_schema()
        schema.update({'language_code': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({'relief_web_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({'hr_info_url': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({'geojson': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({'custom_loc': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({'customization': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        schema.update({
            'activity_level': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
        })
        schema.update({
            'featured_section': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
        })
        schema.update({
            'key_figures': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
        })
        schema.update({
            'data_completeness': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')]
        })
        schema.update({
            'package_count': [tk.get_validator('ignore_missing')]
        })
        schema.update({'display_name': [tk.get_converter('convert_from_extras'), tk.get_validator('ignore_missing')]})
        return schema

    def create(self, country):
        tk.get_action('invalidate_cache_for_groups')({'ignore_auth': True}, {})

    def edit(self, country):
        # invalidate caches
        tk.get_action('invalidate_cache_for_groups')({'ignore_auth': True}, {})

        # Screenshot generation for latest COD when country is edited
        cod_dict = country_helper.get_latest_cod_datatset(country.name)
        shape_infos = []
        if cod_dict:
            shape_infos = [r.get('shape_info') for r in cod_dict.get('resources', []) if r.get('shape_info')]

        if shape_infos and not screenshot.screenshot_exists(cod_dict):
            context = {'ignore_auth': True}
            try:
                tk.get_action('hdx_create_screenshot_for_cod')(context, {'id': cod_dict['id']})
            except Exception, ex:
                log.error(ex)

    # IRoutes
    def before_map(self, map):
        map.connect('%s_index' % group_type, '/%s' % group_type,
                    controller='ckanext.hdx_org_group.controllers.group_controller:HDXGroupController', action='index',
                    highlight_actions='index search')
        map.connect('%s_worldmap' % group_type, '/worldmap',
                    controller='ckanext.hdx_org_group.controllers.group_controller:HDXGroupController', action='group_worldmap')

        map.connect('%s_new' % group_type, '/group/new', controller='group', action='new')

        map.connect('%s_read' % group_type, '/%s/{id}' % group_type,
                    controller='ckanext.hdx_org_group.controllers.country_controller:CountryController', action='country_read')

        map.connect('%s_topline' % group_type, '/%s/topline/{id}' % group_type,
                    controller='ckanext.hdx_org_group.controllers.country_controller:CountryController', action='country_topline')

        return map
