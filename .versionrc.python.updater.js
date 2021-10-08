
function readVersion(contents) {
    let v = contents.match(/__version__ = "(\d+\.\d+\.\d+(-\w+)?)"/);
    if (v === null) {
        return;
    }
    return v[1];
}

function writeVersion(contents, version) {
    console.log('writeVersion', contents, version);
    let v = contents.match(/__version__ = "(\d+\.\d+\.\d+(-\w+)?)"/);
    if (v === null) {
        return contents + `\n__version__ = "${version}"`;
    }
    return contents.replace(/__version__ = "(\d+\.\d+\.\d+(-\w+)?)"/, `__version__ = "${version}"`);
}

module.exports = {
    readVersion,
    writeVersion
}