/**
 * jQuery UI Widget for QR code input
 *
 * @copyright 2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";
    var qrInputID = 0;

    /**
     * qrInput
     */
    $.widget('s3.qrInput', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

            workerPath: null

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = qrInputID;
            qrInputID += 1;

            this.eventNamespace = '.qrInput';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            this.container = $(this.element).closest('.qrinput');
            this.scanButton = $('.qrscan-btn', this.container);

            // Set up qr-scanner worker
            var workerPath = this.options.workerPath;
            if (workerPath) {
                QrScanner.WORKER_PATH = this.options.workerPath;
            }

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            var scanner = this.scanner,
                videoInput = this.videoInput;

            if (scanner) {
                scanner.destroy();
                this.scanner = null;
            }

            if (videoInput) {
                videoInput.remove();
                this.videoInput = null;
            }

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var $el = $(this.element),
                self = this;

            this._unbindEvents();

            $('.error_wrapper', this.container).appendTo(this.container);

            if (self.scanButton.length) {

                QrScanner.hasCamera().then(function(hasCamera) {

                    var scanButton = self.scanButton;

                    if (!hasCamera) {
                        scanButton.prop('disabled', true);
                        return;
                    } else {
                        scanButton.prop('disabled', false);
                    }

                    var scanner,
                        scanForm = $('<div class="qrinput-scan">'),
                        // TODO make success-message configurable
                        success = $('<div class="qrinput-success">').html('<i class="fa fa-check">').hide().appendTo(scanForm),
                        videoInput = $('<video>').appendTo(scanForm);

                    // TODO make width/height configurable or auto-adapt to screen size
                    videoInput.css({width: '300', height: '300'});

                    var dialog = scanForm.dialog({
                        title: 'Scan QR Code',
                        autoOpen: false,
                        modal: true,
                        close: function() {
                            if (scanner) {
                                scanner.stop();
                                scanner.destroy();
                                scanner = null;
                            }
                        }
                    });

                    scanButton.on('click', function() {
                        videoInput.show();
                        success.hide();
                        dialog.dialog('open');
                        scanner = new QrScanner(videoInput.get(0),
                            function(result) {
                                videoInput.hide();
                                success.show();
                                $el.val(result).trigger('change' + self.eventNamespace);
                                setTimeout(function() {
                                    dialog.dialog('close');
                                }, 1000);
                            },
                            function( /* error */ ) {
                                // TODO handle error
                            });

                        scanner.start();
                        // TODO auto-close after timeout?
                    });
                });
            }

            this._bindEvents();
        },

        /**
         * Clear input
         */
        _clearInput: function() {

            $(this.element).val('').trigger('change' + this.eventNamespace);
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var $el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            $('.clear-btn', $el.closest('.qrinput')).on('click' + ns, function() {
                self._clearInput();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var $el = $(this.element),
                ns = this.eventNamespace;

            $('.clear-btn', $el.closest('.qrinput')).off(ns);

            return true;
        }
    });
})(jQuery);
