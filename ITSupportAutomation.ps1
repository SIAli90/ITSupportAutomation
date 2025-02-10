# IT Support Automation Script
Write-Host "Starting IT Support Automation..." -ForegroundColor Cyan


# User Management
PS C:\Windows\system32> $SecurePass = ConvertTo-SecureString "P@ssword123!" -AsPlainText -Force
>> New-ADUser -Name "John Doe" -GivenName "John" -Surname "Doe" `
>>     -UserPrincipalName "johndoe@Domain.local" -SamAccountName "johndoe" `
>>     -Path "OU=Domain Controllers,DC=Domain,DC=local" -AccountPassword $SecurePass `
>>     -Enabled $true -ChangePasswordAtLogon $true
PS C:\Windows\system32> Add-ADGroupMember -Identity "Domain Controllers" -Members "johndoe"

PS C:\Windows\system32> foreach ($user in $inactiveUsers) {
>>     Disable-ADAccount -Identity $user.SamAccountName
>> }
PS C:\Windows\system32> $cutoffDate = (Get-Date).AddDays(-90)
PS C:\Windows\system32> $inactiveUsers = Get-ADUser -Filter * -Properties LastLogonDate | Where-Object {
>>     $_.LastLogonDate -lt $cutoffDate -and $_.Enabled -eq $true
>> }
PS C:\Windows\system32> $inactiveUsers | Select-Object Name, SamAccountName, LastLogonDate


# System Health Monitoring
PS C:\Windows\system32> $cpu = Get-WmiObject win32_processor | Measure-Object -property LoadPercentage -Average | Select-Object Average
PS C:\Windows\system32> $memory = Get-WmiObject win32_operatingsystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory
PS C:\Windows\system32> $disk = Get-PSDrive C | Select-Object Used, Free
PS C:\Windows\system32>
PS C:\Windows\system32> Write-Host "CPU Usage: $($cpu.Average)%"
CPU Usage: 1%
PS C:\Windows\system32> Write-Host "Memory Usage: $([math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory)/$memory.TotalVisibleMemorySize)*100,2))%"
Memory Usage: 13.98%
PS C:\Windows\system32> Write-Host "Disk Space Used: $([math]::Round(($disk.Used / ($disk.Used + $disk.Free) * 100),2))%"
Disk Space Used: 64.13%
PS C:\Windows\system32> if ($cpu.Average -gt 80) {
>>     Write-Host "ALERT: High CPU usage detected!" -ForegroundColor Red
>> }
PS C:\Windows\system32> if (($disk.Used / ($disk.Used + $disk.Free) * 100) -gt 90) {
>>     Write-Host "ALERT: Low disk space!" -ForegroundColor Red
>> }


# Automate Software Deployment
PS C:\Windows\system32> $softwarePath = "C:\Software\Setup.msi"
PS C:\Windows\system32> $softwareName = "PowerAutomate"
PS C:\Windows\system32> $installed = Get-WmiObject -Query "SELECT * FROM Win32_Product WHERE Name = '$softwareName'"
PS C:\Windows\system32> if (-not $installed) {
>>     Write-Host "Installing $softwareName..."
>>     Start-Process "msiexec.exe" -ArgumentList "/i $softwarePath /quiet /norestart" -Wait
>>     Write-Host "$softwareName installed successfully!"
>> } else {
>>     Write-Host "$softwareName is already installed."
>> }


# Automate Network Troubleshooting
PS C:\Windows\system32> $ping = Test-Connection -ComputerName "8.8.8.8" -Count 2 -Quiet
PS C:\Windows\system32> if ($ping) {
>>     Write-Host "Internet is working!"
>> } else {
>>     Write-Host "No internet connection!" -ForegroundColor Red
>> }

PS C:\Windows\system32> Write-Host "Tracing network route to $server..."
PS C:\Windows\system32> tracert $server

