/**
 * Users table view.
 */

require.config({
    paths: {
        'jquery': 'vendor/jquery',
        'underscore': 'vendor/underscore',
        'backbone': 'vendor/backbone',
        'bootstrap': 'vendor/bootstrap',
        'datatables': 'vendor/jquery.dataTables',
        'moment': 'vendor/moment',

        'utils': 'utils',
        'users-collection': 'models/users'
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

define(['utils',
    'users-collection',
    'backbone',
    'bootstrap',
    'moment',
    'datatables'], function (utils, UsersCollection, Backbone, bootstrap, moment) {
        'use strict';

        return Backbone.View.extend({
            el: '#users-page-content',

            events: {
                'click #add-user-btn': 'onAddUser'
            },

            initialize: function () {
                // Create table structure first
                this.createTableStructure();

                // Create users collection
                this.collection = new UsersCollection();

                // Listen to collection events
                this.listenTo(this.collection, 'sync', this.render);
                this.listenTo(this.collection, 'request', this.requestRender);
                this.listenTo(this.collection, 'reset', this.resetRender);
                this.listenTo(this.collection, 'error', this.requestError);

                // Initialize DataTable
                this.table = $('#users-table').DataTable({
                    columns: [
                        { data: 'id' },
                        { data: 'username' },
                        { data: 'category_id' },
                        {
                            data: 'is_admin',
                            render: function (data, type, row) {
                                return data ? 'Yes' : 'No';
                            }
                        },
                        {
                            data: 'is_permission', render: function (data, type, row) {
                                return data ? 'read-only' : 'full-ctrl';
                            }
                        },
                        {
                            data: 'created_at',
                            render: function (data, type, row) {
                                if (!data) return '';
                                return utils.createMoment(data).format('YYYY/MM/DD HH:mm:ss');
                            }
                        },
                        {
                            data: 'updated_at',
                            render: function (data, type, row) {
                                if (!data) return '';
                                return utils.createMoment(data).format('YYYY/MM/DD HH:mm:ss');
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return '<button class="btn btn-primary btn-sm edit-user" data-id="' + row.id + '">Edit</button> ' +
                                    '<button class="btn btn-danger btn-sm delete-user" data-id="' + row.id + '">Delete</button>';
                            }
                        }
                    ],
                    order: [[0, 'asc']],
                    pageLength: 10,
                    searching: true,
                    info: true
                });

                // Load data
                this.resetRender();

                // Bind button events
                var self = this;
                $('#users-table').on('click', '.edit-user', function () {
                    var id = $(this).data('id');
                    self.onEditUser(id);
                });

                $('#users-table').on('click', '.delete-user', function () {
                    var id = $(this).data('id');
                    if (confirm('Are you sure you want to delete this user?')) {
                        self.collection.deleteUser(id);
                    }
                });
            },

            /**
             * Create table structure
             */
            createTableStructure: function () {
                // Build page structure
                var template =
                    '<div class="row">' +
                    '<div class="col-md-12">' +
                    '<div class="panel panel-default">' +
                    '<div class="panel-heading clearfix">' +
                    '<h4 class="panel-title pull-left" style="padding-top: 7.5px;">User Management</h4>' +
                    '<div class="btn-group pull-right">' +
                    '<button id="add-user-btn" class="btn btn-primary btn-sm">Add User</button>' +
                    '</div>' +
                    '</div>' +
                    '<div class="panel-body">' +
                    '<div id="users-spinner"></div>' +
                    '<table id="users-table" class="table table-striped table-hover">' +
                    '<thead>' +
                    '<tr>' +
                    '<th>ID</th>' +
                    '<th>Username</th>' +
                    '<th>Category</th>' +
                    '<th>Admin</th>' +
                    '<th>Permission</th>' +
                    '<th>Created</th>' +
                    '<th>Updated</th>' +
                    '<th>Actions</th>' +
                    '</tr>' +
                    '</thead>' +
                    '<tbody></tbody>' +
                    '</table>' +
                    '</div>' +
                    '</div>' +
                    '</div>' +
                    '</div>' +

                    '<!-- User Form Modal -->' +
                    '<div class="modal fade" id="userFormModal" tabindex="-1" role="dialog" aria-labelledby="userFormModalLabel">' +
                    '<div class="modal-dialog" role="document">' +
                    '<div class="modal-content">' +
                    '<div class="modal-header">' +
                    '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                    '<h4 class="modal-title" id="userFormModalLabel">User Form</h4>' +
                    '</div>' +
                    '<div class="modal-body">' +
                    '<form id="user-form">' +
                    '<input type="hidden" id="user-id">' +
                    '<div class="form-group">' +
                    '<label for="username">Username</label>' +
                    '<input type="text" class="form-control" id="username" placeholder="Enter username">' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label for="password">Password</label>' +
                    '<input type="password" class="form-control" id="password" placeholder="Enter password">' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label for="user-category-id">Category</label>' +
                    '<input type="text" class="form-control" id="user-category-id" placeholder="Enter category ID">' +
                    '</div>' +
                    '<div class="checkbox">' +
                    '<label>' +
                    '<input type="checkbox" id="is-admin"> Admin privileges' +
                    '</label>' +
                    '</div>' +
                    '<div class="checkbox">' +
                    '<label>' +
                    '<input type="checkbox" id="is-permission"> Enable permission' +
                    '</label>' +
                    '</div>' +
                    '</form>' +
                    '</div>' +
                    '<div class="modal-footer">' +
                    '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>' +
                    '<button type="button" class="btn btn-primary" id="save-user">Save</button>' +
                    '</div>' +
                    '</div>' +
                    '</div>' +
                    '</div>';

                $(this.el).html(template);

                // Bind save button event
                var self = this;
                $(document).on('click', '#save-user', function () {
                    self.saveUser();
                });
            },

            /**
             * Add user event handler
             */
            onAddUser: function () {
                // Clear form
                $('#user-id').val('');
                $('#username').val('');
                $('#password').val('');
                $('#user-category-id').val('');
                $('#is-admin').prop('checked', false);
                $('#is-permission').prop('checked', false);

                // Change title
                $('#userFormModalLabel').text('Add User');

                // Show modal
                $('#userFormModal').modal('show');
            },

            /**
             * Edit user event handler
             */
            onEditUser: function (userId) {
                // Find user data
                var user = _.find(this.collection.users, function (user) {
                    return user.get('id') == userId;
                });

                if (user) {
                    // Fill form
                    $('#user-id').val(user.get('id'));
                    $('#username').val(user.get('username'));
                    $('#password').val(''); // Don't show original password
                    $('#user-category-id').val(user.get('category_id') || '');
                    $('#is-admin').prop('checked', user.get('is_admin'));
                    $('#is-permission').prop('checked', user.get('is_permission'));

                    // Change title
                    $('#userFormModalLabel').text('Edit User');

                    // Show modal
                    $('#userFormModal').modal('show');
                }
            },

            /**
             * Save user data
             */
            saveUser: function () {
                var userId = $('#user-id').val();
                var data = {
                    username: $('#username').val(),
                    password: $('#password').val(),
                    category_id: $('#user-category-id').val() || null,
                    is_admin: $('#is-admin').is(':checked'),
                    is_permission: $('#is-permission').is(':checked')
                };

                // Remove password field if empty and in edit mode
                if (!data.password && userId) {
                    delete data.password;
                }

                if (userId) {
                    // Edit mode
                    this.collection.modifyUser(userId, data);
                } else {
                    // Add mode
                    this.collection.addUser(data);
                }

                // Close modal
                $('#userFormModal').modal('hide');
            },

            /**
             * Handle request error
             */
            requestError: function (model, response, options) {
                if (this.spinner) {
                    this.spinner.stop();
                }
                utils.alertError('Request failed: ' + response.responseText);
            },

            /**
             * Handle start of network request
             */
            requestRender: function () {
                if (this.table) {
                    this.table.clear();
                }
                this.spinner = utils.startSpinner('users-spinner');
            },

            /**
             * Reset user data
             */
            resetRender: function (e) {
                if (e) {
                    e.preventDefault();
                }
                this.collection.getUsers();
            },

            /**
             * Render after data fetch is complete
             */
            render: function () {
                var users = this.collection.users;

                if (this.table && users && users.length) {
                    var data = _.map(users, function (user) {
                        return user.toJSON();
                    });

                    this.table.clear();
                    this.table.rows.add(data).draw();
                }

                // Stop loading animation
                if (this.spinner) {
                    this.spinner.stop();
                }
            }
        });
    }); 