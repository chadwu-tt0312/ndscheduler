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
             * Get user count
             */
            getTotal: function () {
                return this.users ? this.users.length : 0;
            },

            /**
             * Get all users
             */
            getUsers: function () {
                this.url = '/api/v1/users';
                this.fetch();
            },

            /**
             * Get single user
             */
            getUser: function (userId) {
                this.url = '/api/v1/users/' + userId;
                this.fetch();
            },

            /**
             * Parse server response
             */
            parse: function (response) {
                console.log('User data response:', response);
                var users = response.users;

                // If API server returns a single user, convert it to an array
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
             * Add user
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
                utils.alertSuccess('User added successfully');
                usersCollection.trigger('reset');
            },

            _addUserError: function (err) {
                utils.alertError('Failed to add user\n' + err.statusText);
            },

            /**
             * Delete user
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
                utils.alertSuccess('User deleted successfully');
                usersCollection.trigger('reset');
            },

            _deleteUserError: function () {
                utils.alertError('Failed to delete user');
            },

            /**
             * Modify user
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
                utils.alertSuccess('User updated successfully');
                usersCollection.trigger('reset');
            },

            _editUserError: function (err) {
                utils.alertError('Failed to update user\n' + err.statusText);
            }
        });
    }); 