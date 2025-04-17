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
             * 獲取分類總數
             */
            getTotal: function () {
                return this.categories ? this.categories.length : 0;
            },

            /**
             * 獲取所有分類
             */
            getCategories: function () {
                this.url = '/api/v1/categories';
                this.fetch();
            },

            /**
             * 獲取單個分類
             */
            getCategory: function (categoryId) {
                this.url = '/api/v1/categories/' + categoryId;
                this.fetch();
            },

            /**
             * 解析服務器返回的響應
             */
            parse: function (response) {
                console.log('分類數據響應:', response);
                var categories = response.categories;

                // 如果 API 服務器返回單個分類，將其轉換為數組
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
             * 添加分類
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
                utils.alertSuccess('成功添加分類');
                categoriesCollection.trigger('reset');
            },

            _addCategoryError: function (err) {
                utils.alertError('添加分類失敗\n' + err.statusText);
            },

            /**
             * 刪除分類
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
                utils.alertSuccess('成功刪除分類');
                categoriesCollection.trigger('reset');
            },

            _deleteCategoryError: function () {
                utils.alertError('刪除分類失敗');
            },

            /**
             * 修改分類
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
                utils.alertSuccess('成功修改分類');
                categoriesCollection.trigger('reset');
            },

            _editCategoryError: function (err) {
                utils.alertError('修改分類失敗\n' + err.statusText);
            }
        });
    }); 