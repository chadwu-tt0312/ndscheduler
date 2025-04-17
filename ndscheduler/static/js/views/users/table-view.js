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
    'datatables'], function (utils, UsersCollection) {
        'use strict';

        return Backbone.View.extend({
            el: '#users-table',

            initialize: function () {
                // 創建用戶集合
                this.collection = new UsersCollection();

                // 監聽集合事件
                this.listenTo(this.collection, 'sync', this.render);
                this.listenTo(this.collection, 'request', this.requestRender);
                this.listenTo(this.collection, 'reset', this.resetRender);
                this.listenTo(this.collection, 'error', this.requestError);

                // 初始化 DataTable
                this.table = $(this.el).DataTable({
                    columns: [
                        { data: 'id' },
                        { data: 'username' },
                        {
                            data: 'is_admin',
                            render: function (data, type, row) {
                                return data ? '是' : '否';
                            }
                        },
                        { data: 'category' },
                        { data: 'permission' },
                        {
                            data: 'created_at',
                            render: function (data, type, row) {
                                if (!data) return '';
                                return moment(data).format('YYYY-MM-DD HH:mm:ss');
                            }
                        },
                        {
                            data: 'updated_at',
                            render: function (data, type, row) {
                                if (!data) return '';
                                return moment(data).format('YYYY-MM-DD HH:mm:ss');
                            }
                        },
                        {
                            data: null,
                            render: function (data, type, row) {
                                return '<button class="btn btn-primary btn-sm edit-user" data-id="' + row.id + '">編輯</button> ' +
                                    '<button class="btn btn-danger btn-sm delete-user" data-id="' + row.id + '">刪除</button>';
                            }
                        }
                    ],
                    order: [[0, 'desc']],
                    pageLength: 10,
                    searching: true,
                    info: true
                });

                // 加載數據
                this.resetRender();

                // 綁定按鈕事件
                var self = this;
                $(this.el).on('click', '.edit-user', function () {
                    var id = $(this).data('id');
                    // 處理編輯操作
                    console.log('編輯用戶：', id);
                });

                $(this.el).on('click', '.delete-user', function () {
                    var id = $(this).data('id');
                    if (confirm('確定要刪除這個用戶嗎？')) {
                        self.collection.deleteUser(id);
                    }
                });
            },

            /**
             * 處理請求錯誤
             */
            requestError: function (model, response, options) {
                this.spinner.stop();
                utils.alertError('請求失敗: ' + response.responseText);
            },

            /**
             * 開始網絡請求時的處理
             */
            requestRender: function () {
                this.table.clear();
                this.spinner = utils.startSpinner('users-spinner');
            },

            /**
             * 重置用戶數據
             */
            resetRender: function (e) {
                if (e) {
                    e.preventDefault();
                }
                this.collection.getUsers();
            },

            /**
             * 完成數據獲取後的渲染
             */
            render: function () {
                var users = this.collection.users;

                if (users && users.length) {
                    var data = _.map(users, function (user) {
                        return user.toJSON();
                    });

                    this.table.clear();
                    this.table.rows.add(data).draw();
                }

                // 停止加載動畫
                if (this.spinner) {
                    this.spinner.stop();
                }
            }
        });
    }); 