/**
 * Audit Log Model
 *
 * @author wenbin@nextdoor.com
 */

require.config({
  paths: {
    'jquery': 'vendor/jquery',
    'underscore': 'vendor/underscore',
    'backbone': 'vendor/backbone',
    'moment': 'vendor/moment',
    'moment-timezone': 'vendor/moment-timezone-with-data',

    'config': 'config'
  },

  shim: {
    'backbone': {
      deps: ['underscore', 'jquery'],
      exports: 'Backbone'
    },
    'moment-timezone': {
      deps: ['moment']
    }
  }
});

define(['config',
  'backbone',
  'moment-timezone'], function (config, backbone, moment) {
    'use strict';

    return Backbone.Model.extend({

      /**
       * Returns html string for job name in logs.
       *
       * @return {string} html string for job name.
       */
      getJobNameHTMLString: function () {
        var jobName = this.get('job_name'),
          jobId = this.get('job_id');
        return '<a href="/#jobs/' + jobId + '">' + jobName + '</a>';
      },

      /**
       * Returns html string for log event type.
       *
       * @return {string} html string for log event type.
       */
      getEventHTMLString: function () {
        var event = this.get('event');
        var style = 'added-color';
        if (event === 'added') {
          style = 'added-color';
        } else if (event === 'custom_run') {
          style = 'custom-run-color';
        } else if (event === 'paused') {
          style = 'paused-color';
        } else if (event === 'resumed') {
          style = 'resumed-color';
        } else if (event === 'deleted') {
          style = 'deleted-color';
        } else if (event === 'modified') {
          style = 'modified-color';
        }
        return '<span class="' + style + '">' + event + '</span>';
      },

      /**
       * Returns event time string.
       *
       * @return {string} event time string.
       */
      getEventTimeString: function () {
        var createdAt = this.get('created_time');
        return moment(createdAt).format('YYYY/MM/DD HH:mm:ss Z');
      },

      /**
       * Returns string for event description.
       *
       * @return {string} string for event description.
       */
      getDescriptionHTMLString: function () {
        var desc = this.get('description');
        var event = this.get('event');
        var descHtml = '';

        if (event === 'custom_run') {
          // TODO (wenbin): Make a beautiful popup window to display this info,
          // instead of linking to raw json.
          descHtml = 'Execution ID: <a href="/#executions/' + desc + '">' + desc + '</a>';
        } else if (event === 'modified') {
          try {
            var changesData = JSON.parse(desc);
            if (changesData && changesData.changes) {
              descHtml = ''; // Start with an empty string
              for (var key in changesData.changes) {
                if (changesData.changes.hasOwnProperty(key)) {
                  var change = changesData.changes[key];
                  var oldValue = typeof change.old === 'object' ? JSON.stringify(change.old) : change.old;
                  var newValue = typeof change.new === 'object' ? JSON.stringify(change.new) : change.new;

                  // Escape HTML entities in values to prevent XSS
                  var escapeHtml = function (unsafe) {
                    return unsafe
                      .replace(/&/g, "&amp;")
                      .replace(/</g, "&lt;")
                      .replace(/>/g, "&gt;")
                      .replace(/"/g, "&quot;")
                      .replace(/'/g, "&#039;");
                  };

                  var formattedOld = escapeHtml(String(oldValue));
                  var formattedNew = escapeHtml(String(newValue));

                  descHtml += '<b>' + escapeHtml(key) + '</b>: <font color="red">' + formattedOld + '</font> => <font color="green">' + formattedNew + '</font><br>';
                }
              }
              // Remove the last <br>
              if (descHtml.endsWith('<br>')) {
                descHtml = descHtml.slice(0, -4);
              }
            } else {
              // If JSON is valid but doesn't have 'changes', display raw desc
              descHtml = desc;
            }
          } catch (e) {
            // If JSON parsing fails, display raw desc
            console.error("Failed to parse description JSON:", e);
            descHtml = desc;
          }
        } else {
          // For other events or if description is empty, return it as is.
          descHtml = desc;
        }

        return descHtml;
      }
    });
  });
