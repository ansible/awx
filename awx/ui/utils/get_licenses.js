#!/usr/bin/env node
/* eslint no-console: ["error", { allow: ["log", "warn", "error"] }] */

const { lstatSync, readdirSync, readFileSync, existsSync, writeFileSync, mkdirSync } = require('fs');
const { join } = require('path');
const licenseTexts = require('./license_texts');

// path to shrinkwrap file
const SHRINKWRAP_PATH = `${__dirname}/../package-lock.json`;
// folder that npm install node_modules to
const NODE_MODULES_FOLDER = `${__dirname}/../node_modules`;
// the folder which we will put the ui license files
const UI_LICENSE_FOLDER = `${__dirname}/../../../docs/licenses/ui`;
// these folders in node_modules should be ommited
const OMITTED_NODE_MODULES_FOLDERS = ['@uirouter', '.bin', 'cycle'];
// all the ways in which deps with license files have license files named
const LICENSE_FILE_NAMES = ['LICENSE', 'LICENCE', 'LICENSE.md', 'LICENSE.txt', 'MIT-LICENSE.txt', 'LICENSE-MIT.txt', 'LICENSE-MIT', 'LICENSE.MIT', 'LICENSE.APACHE2', 'LICENSE.BSD'];
// all the ways in which deps with license info included in readme have the license header
const LICENSE_HEADER_NAMES = ['## License'];
// all the ways in which deps with license info included in readme have readme files named
const README_FILE_NAMES = ['README', 'README.md', 'README.markdown'];
// deps that we need to manually grab the license info (and that info)
const MANUAL_NODE_MODULES_LICENSE_INFO = [];
//     commenting out for now as cycle is a dev dependency,
//     leaving in to show the format expected for this array
//     {
//         module_name: 'cycle',
//         license_info: 'cycle was released as JSON-js
// under the public domain (original repo here: https://github.com/douglascrockford/JSON-js)
// and published to npm as cycle (repo here: https://github.com/dscape/cycle)'
//     }
// ];

// texts of the licenses when the license attr is grabbed from package.json
const LICENSE_TEXTS = licenseTexts;

// below are helper functions the getters and main script execution functions
// call to piece together the license info
const isDirectory = source => lstatSync(source).isDirectory();

const manualNodeModulesSubDirectories = source => [join(source, '@uirouter/angularjs'), join(source, '@uirouter/core')];

const getNonDevDependencyModulesFromShrinkwrap = () => {
    const getModDeps = (deps) => {
        const depNamesArr = Object.keys(deps);
        let arr = [];
        depNamesArr.forEach(name => {
            if (deps[name].dependecies) {
                arr = arr.concat(getModDeps(deps[name].dependecies));
            }
            if (!deps[name].dev) {
                arr.push(name);
            }
        });
        return arr;
    };

    const shrinkwrap = JSON.parse(readFileSync(SHRINKWRAP_PATH).toString());

    return getModDeps(shrinkwrap.dependencies);
};

const getSubdirectories = source => {
    const listOfNonDevDependencyModules = getNonDevDependencyModulesFromShrinkwrap();
    const fromNodeModsDir = readdirSync(source)
        .filter(name => OMITTED_NODE_MODULES_FOLDERS.indexOf(name) === -1)
        .filter(name => listOfNonDevDependencyModules.indexOf(name) !== -1)
        .map(name => join(source, name))
        .filter(isDirectory);
    return fromNodeModsDir.concat(manualNodeModulesSubDirectories(source));
};

const getModulename = path => {
    let updatedPath;
    if (path.includes('@uirouter')) {
        updatedPath = path.split('/').slice(-2).join('-');
    } else {
        updatedPath = path.split('/').slice(-1).join('');
    }

    return updatedPath;
};

const licenseTextIncludedInReadme = (readmeText, returnLicenseText) => LICENSE_HEADER_NAMES
    .reduce((a, b) => {
        let licenseVal;
        if (!returnLicenseText) {
            licenseVal = a || readmeText.includes(b);
        } else if (a !== false) {
            licenseVal = a;
        } else if (readmeText.includes(b)) {
            licenseVal = readmeText.split(b).slice(1, readmeText.split(b).length);
        } else {
            licenseVal = false;
        }
        return licenseVal;
    }, false);

const readmeIncludedInLicense = (path, returnLicenseText) => {
    const readmeText = readFileSync(path).toString();
    return licenseTextIncludedInReadme(readmeText, returnLicenseText);
};

const licenseAttrInPackageJSON = (path, returnLicenseType) => {
    const packageJSON = JSON.parse(readFileSync(path).toString());
    let isInPackageJSON;
    if (!returnLicenseType) {
        isInPackageJSON = packageJSON.license !== undefined || packageJSON.licenses !== undefined;
    } else if (packageJSON.license && packageJSON.license.type) {
        isInPackageJSON = packageJSON.license.type.toString();
    } else if (packageJSON.licenses && Array
        .isArray(packageJSON.licenses) && packageJSON.licenses[0] && packageJSON.licenses[0].type) {
        isInPackageJSON = packageJSON.licenses[0].type.toString();
    } else if (packageJSON.licenses) {
        isInPackageJSON = packageJSON.licenses.toString();
    } else {
        isInPackageJSON = packageJSON.license.toString();
    }
    return isInPackageJSON;
};

// below are getters for the various types of ways licenses are included in the packages

const hasLicenseFile = (path, returnFileName) => LICENSE_FILE_NAMES
    .reduce((a, b) => {
        let isLicenseFile;
        if (!returnFileName) {
            isLicenseFile = a || existsSync(join(path, b));
        } else if (a !== false) {
            isLicenseFile = a;
        } else if (existsSync(join(path, b))) {
            isLicenseFile = join(path, b);
        } else {
            isLicenseFile = false;
        }
        return isLicenseFile;
    }, false);

const hasLicenseAttrInNPM = (path, returnLicenseType) => {
    const packageJSONPath = join(path, 'package.json');
    return existsSync(packageJSONPath) &&
        licenseAttrInPackageJSON(packageJSONPath, returnLicenseType);
};

const hasLicenseInReadme = (path, returnLicenseText) => README_FILE_NAMES
    .reduce((a, b) => {
        const readmePath = join(path, b);
        const readmeIncluded = existsSync(readmePath) && readmeIncludedInLicense(readmePath);
        let isLicenseInReadme;
        if (!returnLicenseText) {
            isLicenseInReadme = a || readmeIncluded;
        } else if (a !== false) {
            isLicenseInReadme = a;
        } else if (readmeIncluded) {
            isLicenseInReadme = readmeIncludedInLicense(readmePath, returnLicenseText);
        } else {
            isLicenseInReadme = false;
        }
        return isLicenseInReadme;
    }, false);

const hasManualLicenseInfo = (path) => Object.prototype.hasOwnProperty
    .call(MANUAL_NODE_MODULES_LICENSE_INFO, path);

// checks to make sure all deps have some sort of license info associated
const licenseCheck = () => {
    console.log('Checking each module for license.');

    const noLicensePackage = getSubdirectories(NODE_MODULES_FOLDER)
        .filter(path => !hasLicenseFile(path) &&
            !hasLicenseAttrInNPM(path) &&
            !hasLicenseInReadme(path) &&
            !hasManualLicenseInfo(path));

    if (noLicensePackage.length === 0) {
        console.log('Success!  All modules probably have a license associated.');
    } else {
        console.log(`ERROR!  The following modules do not have license info associated with them: ${noLicensePackage.join(', ')}.`);
        process.exit(1);
    }
};

// copies the license info from the deps into a licenses folder
const licenseWrite = () => {
    // create the ui license folder if it doesn't exist
    if (!existsSync(UI_LICENSE_FOLDER)) {
        mkdirSync(UI_LICENSE_FOLDER);
    }

    console.log('Copying licenses from modules with license files.');

    const modulesWithLicenseFile = getSubdirectories(NODE_MODULES_FOLDER)
        .filter(path => hasLicenseFile(path));

    console.log(`${modulesWithLicenseFile.length} modules with license files.`);

    modulesWithLicenseFile.forEach(path => {
        writeFileSync(
            join(UI_LICENSE_FOLDER, `${getModulename(path)}.txt`),
            readFileSync(hasLicenseFile(path, true)).toString()
        );
    });

    const modulesWithPackageJSONLicenseAttr = getSubdirectories(NODE_MODULES_FOLDER)
        .filter(path => !hasLicenseFile(path) && hasLicenseAttrInNPM(path));

    console.log(`${modulesWithPackageJSONLicenseAttr.length} modules with license attr in package.json.`);

    modulesWithPackageJSONLicenseAttr.forEach(path => {
        const licenseType = hasLicenseAttrInNPM(path, true);
        const licenseText = LICENSE_TEXTS[licenseType];

        if (!licenseText) {
            console.log(`ERROR!  License text for ${licenseType} is not in license_texts.js.`);
            process.exit(1);
        }

        writeFileSync(join(UI_LICENSE_FOLDER, `${getModulename(path)}.txt`), licenseText);
    });

    const modulesWithLicenseInfoInReadme = getSubdirectories(NODE_MODULES_FOLDER)
        .filter(path => !hasLicenseFile(path) &&
            !hasLicenseAttrInNPM(path) &&
            hasLicenseInReadme(path));

    console.log(`${modulesWithLicenseInfoInReadme.length} modules with license text in readme.`);

    modulesWithLicenseInfoInReadme.forEach(path => {
        writeFileSync(join(UI_LICENSE_FOLDER, `${getModulename(path)}.txt`), hasLicenseInReadme(path, true));
    });

    console.log(`${MANUAL_NODE_MODULES_LICENSE_INFO.length} modules with license info manually added to this script.`);

    MANUAL_NODE_MODULES_LICENSE_INFO.forEach(mod => {
        writeFileSync(join(UI_LICENSE_FOLDER, `${getModulename(mod.module_name)}.txt`), mod.license_info);
    });
};

licenseCheck();
licenseWrite();
