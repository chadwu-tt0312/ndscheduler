/**
 * Users collection
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',

        'utils': 'utils',
        'config': 'config',
        'userModel': 'models/user'
    },

    shim: {
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        }
    }
});

define(['utils',
    'userModel',
    'config',
    'backbone'], function (utils, UserModel, config, backbone) {
        var usersCollection = undefined;

        return Backbone.Collection.extend({
            initialize: function (options) {
                usersCollection = this;
            },

            /**
             * 獲取用戶總數
             */
            getTotal: function () {
                return this.users ? this.users.length : 0;
            },

            /**
             * 獲取所有用戶
             */
            getUsers: function () {
                this.url = '/api/v1/users';
                this.fetch();
            },

            /**
             * 獲取單個用戶
             */
            getUser: function (userId) {
                this.url = '/api/v1/users/' + userId;
                this.fetch();
            },

            /**
             * 解析服務器返回的響應
             */
            parse: function (response) {
                console.log('用戶數據響應:', response);
                var users = response.users;

                // 如果 API 服務器返回單個用戶，將其轉換為數組
                if (!users) {
                    users = [response];
                }

                this.users = [];
                _.each(users, function (user) {
                    this.users.push(new UserModel(user));
                }, this);
                return this.users;
            },

            /**
             * 添加用戶
             */
            addUser: function (data) {
                $.ajax({
                    url: '/api/v1/users',
                    type: 'POST',
                    data: JSON.stringify(data),
                    contentType: 'application/json; charset=utf-8',
                    success: this._addUserSuccess,
                    error: this._addUserError
                });
            },

            _addUserSuccess: function () {
                utils.alertSuccess('成功添加用戶');
                usersCollection.trigger('reset');
            },

            _addUserError: function (err) {
                utils.alertError('添加用戶失敗\n' + err.statusText);
            },

            /**
             * 刪除用戶
             */
            deleteUser: function (userId) {
                $.ajax({
                    url: '/api/v1/users/' + userId,
                    type: 'DELETE',
                    success: this._deleteUserSuccess,
                    error: this._deleteUserError
                });
            },

            _deleteUserSuccess: function () {
                utils.alertSuccess('成功刪除用戶');
                usersCollection.trigger('reset');
            },

            _deleteUserError: function () {
                utils.alertError('刪除用戶失敗');
            },

            /**
             * 修改用戶
             */
            modifyUser: function (userId, data) {
                $.ajax({
                    url: '/api/v1/users/' + userId,
                    type: 'PUT',
                    data: JSON.stringify(data),
                    contentType: 'application/json; charset=utf-8',
                    success: this._editUserSuccess,
                    error: this._editUserError
                });
            },

            _editUserSuccess: function () {
                utils.alertSuccess('成功修改用戶');
                usersCollection.trigger('reset');
            },

            _editUserError: function (err) {
                utils.alertError('修改用戶失敗\n' + err.statusText);
            }
        });
    }); 