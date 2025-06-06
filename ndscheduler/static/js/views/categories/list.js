/**
 * Categories view.
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',
        'bootstrap': 'vendor/bootstrap',
        'datatables': 'vendor/jquery.dataTables',

        'utils': 'utils',
        'categories-table-view': 'views/categories/table-view'
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

define(['categories-table-view',
    'backbone',
    'bootstrap'], function (CategoriesTableView) {

        'use strict';

        return Backbone.View.extend({
            initialize: function () {
                // 初始化分類表格視圖
                new CategoriesTableView();
            }
        });
    }); 