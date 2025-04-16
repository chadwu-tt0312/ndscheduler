define([
    'jquery',
    'underscore',
    'backbone',
    'text!templates/categories/list.html'
], function ($, _, Backbone, listTemplate) {
    'use strict';

    return Backbone.View.extend({
        el: '#content',
        template: _.template(listTemplate),

        events: {
            'click .add-category': 'onAddCategory',
            'click .edit-category': 'onEditCategory',
            'click .delete-category': 'onDeleteCategory'
        },

        initialize: function () {
            this.categories = [];
            this.fetchCategories();
        },

        fetchCategories: function () {
            var self = this;
            $.ajax({
                url: '/api/v1/categories',
                type: 'GET',
                success: function (response) {
                    self.categories = response.categories;
                    self.render();
                },
                error: function (xhr) {
                    alert('Error fetching categories: ' + xhr.responseText);
                }
            });
        },

        render: function () {
            this.$el.html(this.template({
                categories: this.categories
            }));
            return this;
        },

        onAddCategory: function () {
            var name = prompt('Enter category name:');
            if (!name) return;

            var description = prompt('Enter category description (optional):');

            var self = this;
            $.ajax({
                url: '/api/v1/categories',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    name: name,
                    description: description
                }),
                success: function () {
                    self.fetchCategories();
                },
                error: function (xhr) {
                    alert('Error adding category: ' + xhr.responseText);
                }
            });
        },

        onEditCategory: function (e) {
            var categoryId = $(e.target).data('id');
            var category = _.find(this.categories, function (c) {
                return c.id === categoryId;
            });

            var name = prompt('Enter new name:', category.name);
            if (!name) return;

            var description = prompt('Enter new description:', category.description);

            var self = this;
            $.ajax({
                url: '/api/v1/categories/' + categoryId,
                type: 'PUT',
                contentType: 'application/json',
                data: JSON.stringify({
                    name: name,
                    description: description
                }),
                success: function () {
                    self.fetchCategories();
                },
                error: function (xhr) {
                    alert('Error updating category: ' + xhr.responseText);
                }
            });
        },

        onDeleteCategory: function (e) {
            var categoryId = $(e.target).data('id');
            if (!confirm('Are you sure you want to delete this category?')) {
                return;
            }

            var self = this;
            $.ajax({
                url: '/api/v1/categories/' + categoryId,
                type: 'DELETE',
                success: function () {
                    self.fetchCategories();
                },
                error: function (xhr) {
                    alert('Error deleting category: ' + xhr.responseText);
                }
            });
        }
    });
}); 