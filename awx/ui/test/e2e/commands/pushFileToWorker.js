import { basename } from 'path';
import { EventEmitter } from 'events';
import { inherits } from 'util';

import archiver from 'archiver';

function pushFileToWorker (localFilePath, callback) {
    const name = basename(localFilePath);

    const push = handler => {
        const archive = archiver('zip');

        const buffers = [];

        archive
            .on('data', data => buffers.push(data))
            .on('error', err => { throw err; })
            .on('finish', () => {
                const file = Buffer.concat(buffers).toString('base64');

                this.api.session(session => {
                    const params = {
                        path: `/session/${session.sessionId}/file`,
                        method: 'POST',
                        data: { file },
                    };

                    this.client.runProtocolAction(params, handler).send();
                });
            });

        archive.file(localFilePath, { name });
        archive.finalize();
    };

    push(({ status, value }) => {
        if (status !== 0) {
            throw new Error(value.message);
        }

        if (typeof callback === 'function') {
            callback.call(this, value);
        }

        this.emit('complete');
    });

    return this;
}

function PushFileToWorker () { EventEmitter.call(this); }

inherits(PushFileToWorker, EventEmitter);

PushFileToWorker.prototype.command = pushFileToWorker;

module.exports = PushFileToWorker;
