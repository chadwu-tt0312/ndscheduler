/**
 * Category model
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',
        'moment': 'vendor/moment',
        'moment-timezone': 'vendor/moment-timezone-with-data',

        'utils': 'utils'
    },

    shim: {
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        'moment-timezone': {
            deps: ['moment']
        }
    }
});

define(['backbone',
    'moment',
    'moment-timezone',
    'utils'], function (backbone, moment) {
        'use strict';

        return Backbone.Model.extend({
            defaults: {
                id: '',
                name: '',
                description: '',
                created_at: '',
                updated_at: ''
            },

            /**
             * 返回分類創建時間的格式化字符串
             */
            getCreatedAtString: function () {
                if (!this.get('created_at')) {
                    return '';
                }

                var m = moment(this.get('created_at'));
                return m.format('YYYY-MM-DD HH:mm:ss');
            },

            /**
             * 返回分類更新時間的格式化字符串
             */
            getUpdatedAtString: function () {
                if (!this.get('updated_at')) {
                    return '';
                }

                var m = moment(this.get('updated_at'));
                return m.format('YYYY-MM-DD HH:mm:ss');
            }
        });
    }); 