# Nexus Deployment Quality of Life Improvements Plan

## Overview
During the recent deployment of the Nexus agent to moria-pi, several quality-of-life issues were identified that impact developer experience and deployment reliability. This plan outlines the problems encountered and proposes solutions to address them systematically.

## Key Issues Identified

### 1. Network Configuration Complexity
**Problem**: Deployment scripts default to Zerotier IPs but Pis operate on local networks, causing connection failures and requiring manual IP overrides.

**Impact**: 
- Initial deployment failures
- Confusion about which IP to use
- Time wasted on network troubleshooting

**Current State**: Manual environment variable overrides required

### 2. Shared Secret Management
**Problem**: Inconsistent shared secrets between core and agents (`dev-secret` vs `nexus-secret-key-change-in-production`), causing authentication failures.

**Impact**:
- 401 Unauthorized errors during agent registration
- Manual post-deployment fixes required
- Security concerns with hardcoded defaults

**Current State**: Manual synchronization needed

### 3. Systemd Service Configuration Issues
**Problem**: Service configuration conflicts with security settings and uses deprecated options.

**Impact**:
- Service startup failures
- Multiple redeployment attempts needed
- Inconsistent behavior across environments

**Current State**: Manual fixes required after deployment

### 4. Deployment Script Error Handling
**Problem**: Script continues despite failures and lacks post-deployment verification.

**Impact**:
- False success indicators
- Undetected registration failures
- Manual verification required

**Current State**: Limited error checking

### 5. Permission and Directory Management
**Problem**: Incorrect privilege escalation for file system operations.

**Impact**:
- Permission denied errors during setup
- Script failures mid-deployment

**Current State**: Inconsistent use of sudo vs regular ssh commands

### 6. Environment Variable Handling
**Problem**: Hardcoded defaults don't match deployment environments.

**Impact**:
- Agents can't communicate with core
- Network segmentation issues

**Current State**: Manual overrides required

### 7. Manual Post-Deployment Intervention
**Problem**: Several steps require manual SSH access and commands.

**Impact**:
- Not truly automated deployment
- Human error potential
- Time-consuming process

**Current State**: Semi-automated deployment

### 8. Configuration Overwrite During Redeployment
**Problem**: Redeployment scripts overwrite manually modified configuration files (e.g., .env with corrected shared secrets), causing agents to fail authentication again.

**Impact**:
- Agents appear to work initially but fail after restart/redeployment
- Requires manual re-fixing of configurations
- False sense of successful deployment

**Current State**: Configuration changes not preserved across deployments

## Proposed Solutions

### Phase 1: Immediate Fixes (Week 1-2)
1. **Network Configuration**
   - Add `--network-type` flag to deployment scripts
   - Implement IP auto-detection based on reachability
   - Update default configurations to support both Zerotier and local networks

2. **Shared Secret Management**
   - Create centralized secret management system
   - Implement secret generation and distribution script
   - Update all components to use consistent secret sources

3. **Systemd Service Fixes**
   - Fix PATH issues in ExecStartPre
   - Replace deprecated MemoryLimit with MemoryMax
   - Adjust security settings for functionality

### Phase 2: Enhanced Automation (Week 3-4)
4. **Error Handling and Verification**
   - Add comprehensive error checking throughout scripts
   - Implement post-deployment health checks
   - Add rollback capabilities for failed deployments

5. **Permission Management**
   - Audit all remote commands for proper privilege handling
   - Standardize sudo usage patterns
   - Implement proper file permission management

### Phase 3: Configuration Management (Week 5-6)
6. **Environment Configuration**
   - Implement configuration file system
   - Support multiple deployment environments
   - Add validation for configuration consistency

7. **Deployment Automation**
   - Eliminate manual intervention requirements
   - Add retry logic for transient failures
   - Implement comprehensive logging and monitoring

8. **Configuration Preservation**
   - Implement configuration backup/restore during redeployment
   - Add validation to detect and preserve manual changes
   - Use configuration templating with variable substitution

## Implementation Plan

### Week 1: Core Fixes
- [ ] Fix systemd service configuration
- [ ] Implement consistent sudo usage
- [ ] Add basic error checking to deployment scripts

### Week 2: Network and Secrets
- [ ] Add network type detection
- [ ] Implement centralized secret management
- [ ] Update default configurations

### Week 3: Verification and Monitoring
- [ ] Add post-deployment verification
- [ ] Implement health check endpoints
- [ ] Add comprehensive logging

### Week 4: Configuration System
- [ ] Design configuration file format
- [ ] Implement validation system
- [ ] Update all scripts to use new config

### Week 5: Testing and Documentation
- [ ] Create integration tests for deployments
- [ ] Update documentation with new procedures
- [ ] Test across different network configurations

### Week 6: Rollout and Training
- [ ] Deploy improvements to staging
- [ ] Update deployment guides
- [ ] Train team on new procedures

## Success Metrics

### Quantitative
- Deployment success rate: Target 95%+ (currently ~70%)
- Average deployment time: Reduce from 30+ minutes to <15 minutes
- Manual intervention points: Reduce from 5+ to 0

### Qualitative
- Developer satisfaction with deployment process
- Reduced troubleshooting time
- Improved reliability across network types

## Resources Required

### Personnel
- 1 Senior DevOps Engineer (lead)
- 1 Backend Developer (core integration)
- 1 DevOps Engineer (scripting)

### Tools/Infrastructure
- Access to test Pis across different networks
- CI/CD pipeline updates
- Configuration management system

## Risk Assessment

### High Risk
- Network configuration changes could break existing deployments
- Secret management changes could impact security

### Mitigation
- Thorough testing in staging environment
- Gradual rollout with rollback capabilities
- Security review of all changes

## Dependencies

- Core team availability for testing
- Access to all Pi devices for validation
- Approval for configuration management tool selection

## Next Steps

1. Schedule kickoff meeting with stakeholders
2. Assign team members to phases
3. Set up testing environments
4. Begin Phase 1 implementation

---

**Document Version**: 1.0  
**Date**: March 14, 2026  
**Author**: GitHub Copilot  
**Review Date**: March 21, 2026</content>
<parameter name="filePath">/home/methinked/Projects/nexus/nexus/docs/plans/deployment-qol-improvements-plan.md