/**
 * Users view.
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',
        'bootstrap': 'vendor/bootstrap',
        'datatables': 'vendor/jquery.dataTables',

        'utils': 'utils',
        'users-table-view': 'views/users/table-view'
    },

    shim: {
        'bootstrap': {
            deps: ['jquery']
        },
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        'datatables': {
            deps: ['jquery'],
            exports: '$.fn.dataTable'
        }
    }
});

define(['users-table-view',
    'backbone',
    'bootstrap'], function (UsersTableView) {

        'use strict';

        return Backbone.View.extend({
            initialize: function () {
                // 初始化用戶表格視圖
                new UsersTableView();
            }
        });
    }); 