/**
 * Categories table view.
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
        'categories-collection': 'models/categories'
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
    'categories-collection',
    'backbone',
    'bootstrap',
    'moment',
    'datatables'], function (utils, CategoriesCollection, Backbone, bootstrap, moment) {
        'use strict';

        return Backbone.View.extend({
            el: '#categories-page-content',

            events: {
                'click #add-category-btn': 'onAddCategory'
            },

            initialize: function () {
                // Create table structure first
                this.createTableStructure();

                // Create categories collection
                this.collection = new CategoriesCollection();

                // Listen to collection events
                this.listenTo(this.collection, 'sync', this.render);
                this.listenTo(this.collection, 'request', this.requestRender);
                this.listenTo(this.collection, 'reset', this.resetRender);
                this.listenTo(this.collection, 'error', this.requestError);

                // Initialize DataTable
                this.table = $('#categories-table').DataTable({
                    columns: [
                        { data: 'id' },
                        { data: 'name' },
                        { data: 'description' },
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
                                return '<button class="btn btn-primary btn-sm edit-category" data-id="' + row.id + '">Edit</button> ' +
                                    '<button class="btn btn-danger btn-sm delete-category" data-id="' + row.id + '">Delete</button>';
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
                $('#categories-table').on('click', '.edit-category', function () {
                    var id = $(this).data('id');
                    self.onEditCategory(id);
                });

                $('#categories-table').on('click', '.delete-category', function () {
                    var id = $(this).data('id');
                    if (confirm('Are you sure you want to delete this category?')) {
                        self.collection.deleteCategory(id);
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
                    '<h4 class="panel-title pull-left" style="padding-top: 7.5px;">Category Management</h4>' +
                    '<div class="btn-group pull-right">' +
                    '<button id="add-category-btn" class="btn btn-primary btn-sm">Add Category</button>' +
                    '</div>' +
                    '</div>' +
                    '<div class="panel-body">' +
                    '<div id="categories-spinner"></div>' +
                    '<table id="categories-table" class="table table-striped table-hover">' +
                    '<thead>' +
                    '<tr>' +
                    '<th>ID</th>' +
                    '<th>Name</th>' +
                    '<th>Description</th>' +
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

                    '<!-- Category Form Modal -->' +
                    '<div class="modal fade" id="categoryFormModal" tabindex="-1" role="dialog" aria-labelledby="categoryFormModalLabel">' +
                    '<div class="modal-dialog" role="document">' +
                    '<div class="modal-content">' +
                    '<div class="modal-header">' +
                    '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
                    '<h4 class="modal-title" id="categoryFormModalLabel">Category Form</h4>' +
                    '</div>' +
                    '<div class="modal-body">' +
                    '<form id="category-form">' +
                    '<input type="hidden" id="category-id">' +
                    '<div class="form-group">' +
                    '<label for="name">Name</label>' +
                    '<input type="text" class="form-control" id="name" placeholder="Enter category name">' +
                    '</div>' +
                    '<div class="form-group">' +
                    '<label for="description">Description</label>' +
                    '<textarea class="form-control" id="description" placeholder="Enter category description"></textarea>' +
                    '</div>' +
                    '</form>' +
                    '</div>' +
                    '<div class="modal-footer">' +
                    '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>' +
                    '<button type="button" class="btn btn-primary" id="save-category">Save</button>' +
                    '</div>' +
                    '</div>' +
                    '</div>' +
                    '</div>';

                $(this.el).html(template);

                // Bind save button event
                var self = this;
                $(document).on('click', '#save-category', function () {
                    self.saveCategory();
                });
            },

            /**
             * Add category event handler
             */
            onAddCategory: function () {
                // Clear form
                $('#category-id').val('');
                $('#name').val('');
                $('#description').val('');

                // Change title
                $('#categoryFormModalLabel').text('Add Category');

                // Show modal
                $('#categoryFormModal').modal('show');
            },

            /**
             * Edit category event handler
             */
            onEditCategory: function (categoryId) {
                // Find category data
                var category = _.find(this.collection.categories, function (category) {
                    return category.get('id') == categoryId;
                });

                if (category) {
                    // Fill form
                    $('#category-id').val(category.get('id'));
                    $('#name').val(category.get('name'));
                    $('#description').val(category.get('description') || '');

                    // Change title
                    $('#categoryFormModalLabel').text('Edit Category');

                    // Show modal
                    $('#categoryFormModal').modal('show');
                }
            },

            /**
             * Save category data
             */
            saveCategory: function () {
                var categoryId = $('#category-id').val();
                var data = {
                    name: $('#name').val(),
                    description: $('#description').val() || null
                };

                if (categoryId) {
                    // Edit mode
                    this.collection.modifyCategory(categoryId, data);
                } else {
                    // Add mode
                    this.collection.addCategory(data);
                }

                // Close modal
                $('#categoryFormModal').modal('hide');
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
                this.spinner = utils.startSpinner('categories-spinner');
            },

            /**
             * Reset category data
             */
            resetRender: function (e) {
                if (e) {
                    e.preventDefault();
                }
                this.collection.getCategories();
            },

            /**
             * Render after data fetch is complete
             */
            render: function () {
                var categories = this.collection.categories;

                if (this.table && categories && categories.length) {
                    var data = _.map(categories, function (category) {
                        return category.toJSON();
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