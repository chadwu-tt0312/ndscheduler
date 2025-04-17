/**
 * Categories collection
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',

        'utils': 'utils',
        'config': 'config',
        'categoryModel': 'models/category'
    },

    shim: {
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        }
    }
});

define(['utils',
    'categoryModel',
    'config',
    'backbone'], function (utils, CategoryModel, config, backbone) {
        var categoriesCollection = undefined;

        return Backbone.Collection.extend({
            initialize: function (options) {
                categoriesCollection = this;
            },

            /**
             * Get category count
             */
            getTotal: function () {
                return this.categories ? this.categories.length : 0;
            },

            /**
             * Get all categories
             */
            getCategories: function () {
                this.url = '/api/v1/categories';
                this.fetch();
            },

            /**
             * Get single category
             */
            getCategory: function (categoryId) {
                this.url = '/api/v1/categories/' + categoryId;
                this.fetch();
            },

            /**
             * Parse server response
             */
            parse: function (response) {
                console.log('Category data response:', response);
                var categories = response.categories;

                // If API server returns a single category, convert it to an array
                if (!categories) {
                    categories = [response];
                }

                this.categories = [];
                _.each(categories, function (category) {
                    this.categories.push(new CategoryModel(category));
                }, this);
                return this.categories;
            },

            /**
             * Add category
             */
            addCategory: function (data) {
                $.ajax({
                    url: '/api/v1/categories',
                    type: 'POST',
                    data: JSON.stringify(data),
                    contentType: 'application/json; charset=utf-8',
                    success: this._addCategorySuccess,
                    error: this._addCategoryError
                });
            },

            _addCategorySuccess: function () {
                utils.alertSuccess('Category added successfully');
                categoriesCollection.trigger('reset');
            },

            _addCategoryError: function (err) {
                utils.alertError('Failed to add category\n' + err.statusText);
            },

            /**
             * Delete category
             */
            deleteCategory: function (categoryId) {
                $.ajax({
                    url: '/api/v1/categories/' + categoryId,
                    type: 'DELETE',
                    success: this._deleteCategorySuccess,
                    error: this._deleteCategoryError
                });
            },

            _deleteCategorySuccess: function () {
                utils.alertSuccess('Category deleted successfully');
                categoriesCollection.trigger('reset');
            },

            _deleteCategoryError: function () {
                utils.alertError('Failed to delete category');
            },

            /**
             * Modify category
             */
            modifyCategory: function (categoryId, data) {
                $.ajax({
                    url: '/api/v1/categories/' + categoryId,
                    type: 'PUT',
                    data: JSON.stringify(data),
                    contentType: 'application/json; charset=utf-8',
                    success: this._editCategorySuccess,
                    error: this._editCategoryError
                });
            },

            _editCategorySuccess: function () {
                utils.alertSuccess('Category updated successfully');
                categoriesCollection.trigger('reset');
            },

            _editCategoryError: function (err) {
                utils.alertError('Failed to update category\n' + err.statusText);
            }
        });
    }); 