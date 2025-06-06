# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=unused-import

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class BackupVaultScenarioTest(ScenarioTest):

    def setUp(test):
        super().setUp()
        test.kwargs.update({
            'location': 'centraluseuap',
            'vaultName': 'cli-test-backup-vault',
            'uamiVaultName': 'cli-test-backup-uami-vault',
        })

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='clitest-dpp-backupvault-', location='centraluseuap')
    def test_dataprotection_backup_vault_create_and_delete(test):
        test.cmd('az dataprotection backup-vault create '
                 '-g "{rg}" --vault-name "{vaultName}" -l "{location}" '
                 '--storage-settings datastore-type="VaultStore" type="GeoRedundant" --type "SystemAssigned" '
                 '--immutability-state "Locked" --cross-region-restore-state "Enabled"',
                 checks=[
                     test.check('name', "{vaultName}"),
                     test.check('identity.type', "SystemAssigned"),
                     test.check('properties.securitySettings.softDeleteSettings.state', "On"),
                     test.check('properties.securitySettings.softDeleteSettings.retentionDurationInDays', 14.0),
                     test.check('properties.securitySettings.immutabilitySettings.state', "Locked"),
                     test.check('properties.storageSettings[0].datastoreType', "VaultStore"),
                     test.check('properties.storageSettings[0].type', "GeoRedundant"),
                     test.check('properties.featureSettings.crossRegionRestoreSettings.state', "Enabled")
                 ])
        test.cmd('az dataprotection backup-vault list -g "{rg}"', checks=[
            test.check("length([?name == '{vaultName}'])", 1),
            test.exists("[?name == '{vaultName}']")   # Better way to check existance ?.
        ])
        test.cmd('az dataprotection backup-vault show -g "{rg}" --vault-name "{vaultName}"', checks=[
            test.check('name', "{vaultName}")
        ])
        test.cmd('az dataprotection backup-vault delete -g "{rg}" --vault-name "{vaultName}" -y')
        
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='clitest-dpp-backupvault-', location='centraluseuap')
    def test_dataprotection_backup_vault_create_with_uami_update_and_delete(test):
        test.kwargs.update({
            'uamiUrl': "/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourcegroups/clitest-dpp-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/cmk-cli-test-uami",
            'uamiName': "cmk-cli-test-uami",
        })
        test.cmd('az dataprotection backup-vault create '
                 '-g "{rg}" --vault-name "{uamiVaultName}" -l "{location}" '
                 '--storage-settings datastore-type="VaultStore" type="GeoRedundant" --type "UserAssigned" '
                 '--uami {{"{uamiUrl}":{{}}}} ',
                 checks=[
                     test.check('name', "{uamiVaultName}"),
                     test.check('identity.type', "UserAssigned"),
                 ])

        test.cmd('az dataprotection backup-vault update '
                 '-g "{rg}" -v "{uamiVaultName}" --type "SystemAssigned,UserAssigned"',
                 checks=[
                     test.check('identity.type', 'SystemAssigned,UserAssigned')
                 ]) 

        test.cmd('az dataprotection backup-vault update '
                 '-g "{rg}" -v "{uamiVaultName}" --type "SystemAssigned"',
                 checks=[
                     test.check('identity.type', 'SystemAssigned')
                 ]) 

        test.cmd('az dataprotection backup-vault update '
                 '-g "{rg}" -v "{uamiVaultName}" --type "None"',
                 checks=[
                     test.check('identity.type', 'None')
                 ]) 

        # test.cmd('az dataprotection backup-vault update '
        #          '-g "{rg}" -v "{uamiVaultName}" '
        #          '--type "UserAssigned"'
        #          '--uami {{"{uamiUrl}":{{}}}} ',
        #          checks=[
        #              test.check('identity.type', 'UserAssigned')
        #          ]) 

        test.cmd('az dataprotection backup-vault delete -g "{rg}" --vault-name "{uamiVaultName}" -y')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='clitest-dpp-backupvault-', location='centraluseuap')
    def test_dataprotection_backup_vault_create_with_cmk_update_and_delete(test):
        test.kwargs.update({
            'cmkKeyUri': "https://cmk-cli-test-keyvault.vault.azure.net/keys/cmk-cli-key1/24efffaddbe84838a1c39b6135edbdf5",
            'cmkKeyUriUpdate': "https://cmk-cli-test-keyvault.vault.azure.net/keys/cmk-cli-key2/864fe3c0fcf14d75bd7d576a148ba51c",
            'cmkUami': "/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourcegroups/clitest-dpp-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/cmk-cli-test-uami",
            'cmkUamiName': "cmk-cli-test-uami",
        })
        test.cmd('az dataprotection backup-vault create '
                 '-g "{rg}" --vault-name "{vaultName}" -l "{location}" '
                 '--storage-settings datastore-type="VaultStore" type="GeoRedundant" --type "UserAssigned" '
                 '--user-assigned-identities {{"{cmkUami}":{{}}}} --cmk-encryption-key-uri "{cmkKeyUri}" '
                 '--cmk-encryption-state Enabled --cmk-identity-type UserAssigned '
                 '--cmk-infrastructure-encryption Enabled --cmk-user-assigned-identity-id  "{cmkUami}" ',
                 checks=[
                     test.check('name', "{vaultName}"),
                     test.check('identity.type', "UserAssigned"),
                     test.check('properties.securitySettings.encryptionSettings.state', "Enabled"),
                     test.check('properties.securitySettings.encryptionSettings.infrastructureEncryption', "Enabled"),
                     test.check('properties.securitySettings.encryptionSettings.keyVaultProperties.keyUri', "{cmkKeyUri}"),
                     test.check("contains(properties.securitySettings.encryptionSettings.kekIdentity.identityId, '/{cmkUamiName}')", True),
                     test.check('properties.securitySettings.encryptionSettings.kekIdentity.identityType', "UserAssigned")
                 ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --cmk-encryption-key-uri "{cmkKeyUriUpdate}"', checks=[
            test.check('properties.securitySettings.encryptionSettings.keyVaultProperties.keyUri', "{cmkKeyUriUpdate}"),
        ])
        test.cmd('az dataprotection backup-vault delete -g "{rg}" --vault-name "{vaultName}" -y')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='clitest-dpp-backupvault-', location='centraluseuap')
    def test_dataprotection_backup_vault_update(test):
        test.cmd('az dataprotection backup-vault create '
                 '-g "{rg}" --vault-name "{vaultName}" -l "{location}" '
                 '--storage-settings datastore-type="VaultStore" type="GeoRedundant" --type "SystemAssigned" '
                 '--soft-delete-state "Off" --immutability-state "Unlocked"',
                 checks=[
                     test.check('properties.featureSettings.crossRegionRestoreSettings.state', "None")
                 ])

        # soft-delete updates
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --soft-delete-state "On" --retention-duration-in-days "14"', checks=[
            test.check('properties.securitySettings.softDeleteSettings.state', "On"),
            test.check('properties.securitySettings.softDeleteSettings.retentionDurationInDays', 14.0)
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --soft-delete-state "Off"', checks=[
            test.check('properties.securitySettings.softDeleteSettings.state', "Off")
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --soft-delete-state "AlwaysOn"', checks=[
            test.check('properties.securitySettings.softDeleteSettings.state', "AlwaysOn"),
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --soft-delete-state "On"', expect_failure=True)

        # azure-monitor-alerts-for-job-failures updates
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --azure-monitor-alerts-for-job-failures enabled', checks=[
            test.check('properties.monitoringSettings.azureMonitorAlertSettings.alertsForAllJobFailures', 'Enabled')
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --azure-monitor-alerts-for-job-failures disabled', checks=[
            test.check('properties.monitoringSettings.azureMonitorAlertSettings.alertsForAllJobFailures', 'Disabled')
        ])

        # immutability-state updates
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --immutability-state "Disabled"', checks=[
            test.check('properties.securitySettings.immutabilitySettings.state', "Disabled")
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --immutability-state "Locked"', checks=[
            test.check('properties.securitySettings.immutabilitySettings.state', "Locked")
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --immutability-state "Unlocked"', expect_failure=True)

        # Cross-region restore updates
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --crr-state "Enabled"', checks=[
            test.check('properties.featureSettings.crossRegionRestoreSettings.state', "Enabled")
        ])
        test.cmd('az dataprotection backup-vault update -g "{rg}" --vault-name "{vaultName}" --cross-region-restore-state "Disabled"', expect_failure=True)

        test.cmd('az dataprotection backup-vault delete -g "{rg}" --vault-name "{vaultName}" -y')