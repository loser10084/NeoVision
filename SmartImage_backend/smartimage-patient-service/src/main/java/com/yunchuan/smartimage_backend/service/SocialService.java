package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.dto.ConsultationCreateRequest;
import com.yunchuan.smartimage_backend.dto.ConsultationMessageSendRequest;
import com.yunchuan.smartimage_backend.entity.*;
import com.yunchuan.smartimage_backend.mapper.*;
import com.yunchuan.smartimage_backend.utils.AliOssUtil;
import com.yunchuan.smartimage_backend.vo.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class SocialService {

    private static final int DEFAULT_MESSAGE_LIMIT = 50;
    private static final int MAX_MESSAGE_LIMIT = 200;
    private static final Set<String> SUPPORTED_MESSAGE_TYPES = Set.of("TEXT", "FILE", "IMAGE", "MODEL", "LINK");

    private final DoctorSocialMapper doctorSocialMapper;
    private final PatientMapper patientMapper;
    private final ConsultationSessionMapper consultationSessionMapper;
    private final ConsultationMemberMapper consultationMemberMapper;
    private final ConsultationMessageMapper consultationMessageMapper;
    private final AliOssUtil aliOssUtil;

    public SocialService(DoctorSocialMapper doctorSocialMapper,
                         PatientMapper patientMapper,
                         ConsultationSessionMapper consultationSessionMapper,
                         ConsultationMemberMapper consultationMemberMapper,
                         ConsultationMessageMapper consultationMessageMapper,
                         AliOssUtil aliOssUtil) {
        this.doctorSocialMapper = doctorSocialMapper;
        this.patientMapper = patientMapper;
        this.consultationSessionMapper = consultationSessionMapper;
        this.consultationMemberMapper = consultationMemberMapper;
        this.consultationMessageMapper = consultationMessageMapper;
        this.aliOssUtil = aliOssUtil;
    }

    public List<DoctorSimpleVO> searchDoctors(Long currentUserId, String keyword) {
        Set<Long> friendIds = new HashSet<>(doctorSocialMapper.listFriendIds(currentUserId));
        List<DoctorUser> doctors = doctorSocialMapper.searchDoctors(currentUserId, keyword);
        return doctors.stream().map(doctor -> {
            DoctorSimpleVO vo = new DoctorSimpleVO();
            vo.setId(doctor.getId());
            vo.setName(doctor.getName());
            vo.setHospital(doctor.getHospital());
            vo.setDept(doctor.getDept());
            vo.setMobile(doctor.getMobile());
            vo.setFriend(friendIds.contains(doctor.getId()));
            return vo;
        }).collect(Collectors.toList());
    }

    public List<DoctorSimpleVO> listFriends(Long currentUserId) {
        return doctorSocialMapper.listFriends(currentUserId);
    }

    @Transactional
    public void addFriend(Long currentUserId, Long friendId) {
        if (friendId == null || Objects.equals(currentUserId, friendId)) {
            throw new BusinessException(400, "invalid friend id");
        }
        if (doctorSocialMapper.findById(friendId) == null) {
            throw new BusinessException(404, "friend not found");
        }
        long[] pair = normalizePair(currentUserId, friendId);
        if (doctorSocialMapper.countFriendPair(pair[0], pair[1]) > 0) {
            return;
        }
        DoctorFriend relation = new DoctorFriend();
        relation.setDoctorId(pair[0]);
        relation.setFriendId(pair[1]);
        relation.setCreatedBy(currentUserId);
        doctorSocialMapper.insertFriend(relation);
    }

    @Transactional
    public void removeFriend(Long currentUserId, Long friendId) {
        if (friendId == null || Objects.equals(currentUserId, friendId)) {
            throw new BusinessException(400, "invalid friend id");
        }
        long[] pair = normalizePair(currentUserId, friendId);
        if (doctorSocialMapper.deleteFriend(pair[0], pair[1]) == 0) {
            throw new BusinessException(404, "friend relation not found");
        }
    }

    public List<ConsultationVO> listConsultations(Long currentUserId) {
        return consultationSessionMapper.listByDoctor(currentUserId);
    }

    @Transactional
    public ConsultationVO createConsultation(Long currentUserId, ConsultationCreateRequest request) {
        if (request == null || !StringUtils.hasText(request.getTitle())) {
            throw new BusinessException(400, "title is required");
        }
        Long patientId = request.getPatientId();
        if (patientId != null) {
            if (patientId <= 0) {
                throw new BusinessException(400, "invalid patientId");
            }
            if (patientMapper.findById(patientId) == null) {
                throw new BusinessException(404, "patient not found: " + patientId);
            }
        }
        ConsultationSession session = new ConsultationSession();
        session.setTitle(request.getTitle().trim());
        session.setPatientId(patientId);
        session.setCreatorId(currentUserId);
        session.setStatus("ACTIVE");
        session.setMaterialsOssPath(trimToNull(request.getMaterialsOssPath()));
        consultationSessionMapper.insert(session);

        ConsultationMember owner = new ConsultationMember();
        owner.setConsultationId(session.getId());
        owner.setDoctorId(currentUserId);
        owner.setRole("OWNER");
        consultationMemberMapper.insert(owner);

        if (request.getMemberIds() != null) {
            for (Long memberId : request.getMemberIds().stream().filter(Objects::nonNull).distinct().collect(Collectors.toList())) {
                if (Objects.equals(memberId, currentUserId)) {
                    continue;
                }
                if (doctorSocialMapper.findById(memberId) == null) {
                    throw new BusinessException(404, "member not found: " + memberId);
                }
                long[] pair = normalizePair(currentUserId, memberId);
                if (doctorSocialMapper.countFriendPair(pair[0], pair[1]) == 0) {
                    throw new BusinessException(400, "member is not your friend: " + memberId);
                }
                if (consultationMemberMapper.countMember(session.getId(), memberId) == 0) {
                    ConsultationMember member = new ConsultationMember();
                    member.setConsultationId(session.getId());
                    member.setDoctorId(memberId);
                    member.setRole("MEMBER");
                    consultationMemberMapper.insert(member);
                }
            }
        }

        return consultationSessionMapper.findVOById(session.getId());
    }

    public List<ConsultationMemberVO> listMembers(Long consultationId, Long currentUserId) {
        ensureMember(consultationId, currentUserId);
        return consultationMemberMapper.listMembers(consultationId);
    }

    @Transactional
    public void addMember(Long consultationId, Long doctorId, Long currentUserId) {
        ConsultationSession session = ensureOwner(consultationId, currentUserId);
        if (doctorId == null) {
            throw new BusinessException(400, "doctorId is required");
        }
        if (doctorSocialMapper.findById(doctorId) == null) {
            throw new BusinessException(404, "doctor not found");
        }
        long[] pair = normalizePair(currentUserId, doctorId);
        if (doctorSocialMapper.countFriendPair(pair[0], pair[1]) == 0) {
            throw new BusinessException(400, "doctor is not your friend");
        }
        if (consultationMemberMapper.countMember(session.getId(), doctorId) > 0) {
            return;
        }
        ConsultationMember member = new ConsultationMember();
        member.setConsultationId(session.getId());
        member.setDoctorId(doctorId);
        member.setRole("MEMBER");
        consultationMemberMapper.insert(member);
    }

    @Transactional
    public void removeMember(Long consultationId, Long doctorId, Long currentUserId) {
        ConsultationSession session = ensureOwner(consultationId, currentUserId);
        if (doctorId == null) {
            throw new BusinessException(400, "doctorId is required");
        }
        if (Objects.equals(session.getCreatorId(), doctorId)) {
            throw new BusinessException(400, "owner cannot be removed");
        }
        if (consultationMemberMapper.deleteMember(consultationId, doctorId) == 0) {
            throw new BusinessException(404, "member not found");
        }
    }

    public List<ConsultationMessageVO> listMessages(Long consultationId, Long currentUserId, Long beforeId, Integer limit) {
        ensureMember(consultationId, currentUserId);
        int finalLimit = limit == null ? DEFAULT_MESSAGE_LIMIT : Math.max(1, Math.min(limit, MAX_MESSAGE_LIMIT));
        return consultationMessageMapper.listMessages(consultationId, beforeId, finalLimit);
    }

    @Transactional
    public ConsultationMessageVO sendMessage(Long consultationId, Long currentUserId, ConsultationMessageSendRequest request) {
        ensureMember(consultationId, currentUserId);
        if (request == null) {
            throw new BusinessException(400, "request is required");
        }
        String messageType = normalizeMessageType(request.getMessageType(), "TEXT");
        String textContent = trimToNull(request.getTextContent());
        String ossPath = trimToNull(request.getOssPath());

        if ("TEXT".equals(messageType)) {
            if (!StringUtils.hasText(textContent)) {
                throw new BusinessException(400, "textContent is required for TEXT message");
            }
        } else if (!StringUtils.hasText(ossPath)) {
            throw new BusinessException(400, "ossPath is required for non-TEXT message");
        }

        ConsultationMessage message = new ConsultationMessage();
        message.setConsultationId(consultationId);
        message.setSenderId(currentUserId);
        message.setMessageType(messageType);
        message.setTextContent(textContent);
        message.setOssPath(ossPath);
        message.setFileName(trimToNull(request.getFileName()));
        message.setFileSize(request.getFileSize());
        message.setMimeType(trimToNull(request.getMimeType()));
        consultationMessageMapper.insert(message);
        consultationSessionMapper.touch(consultationId);
        return consultationMessageMapper.findVOById(message.getId());
    }

    @Transactional
    public ConsultationMessageVO uploadAttachment(Long consultationId,
                                                  Long currentUserId,
                                                  MultipartFile file,
                                                  String messageType) {
        ensureMember(consultationId, currentUserId);
        if (file == null || file.isEmpty()) {
            throw new BusinessException(400, "empty file");
        }

        String finalType = normalizeMessageType(messageType, "FILE");
        if ("TEXT".equals(finalType)) {
            finalType = "FILE";
        }

        byte[] bytes;
        try {
            bytes = file.getBytes();
        } catch (IOException e) {
            throw new BusinessException(500, "read file failed: " + e.getMessage());
        }

        String objectName = buildAttachmentObjectName(consultationId, file.getOriginalFilename());
        String ossPath;
        try {
            ossPath = aliOssUtil.upload(bytes, objectName);
        } catch (Exception e) {
            throw new BusinessException(500, "upload attachment failed: " + e.getMessage());
        }

        ConsultationMessage message = new ConsultationMessage();
        message.setConsultationId(consultationId);
        message.setSenderId(currentUserId);
        message.setMessageType(finalType);
        message.setTextContent(null);
        message.setOssPath(ossPath);
        message.setFileName(file.getOriginalFilename());
        message.setFileSize(file.getSize());
        message.setMimeType(file.getContentType());
        consultationMessageMapper.insert(message);
        consultationSessionMapper.touch(consultationId);
        return consultationMessageMapper.findVOById(message.getId());
    }

    private ConsultationSession ensureOwner(Long consultationId, Long currentUserId) {
        ConsultationSession session = consultationSessionMapper.findById(consultationId);
        if (session == null) {
            throw new BusinessException(404, "consultation not found");
        }
        if (!Objects.equals(session.getCreatorId(), currentUserId)) {
            throw new BusinessException(403, "only owner can operate this action");
        }
        ensureMember(consultationId, currentUserId);
        return session;
    }

    private void ensureMember(Long consultationId, Long currentUserId) {
        ConsultationSession session = consultationSessionMapper.findById(consultationId);
        if (session == null) {
            throw new BusinessException(404, "consultation not found");
        }
        if (consultationMemberMapper.countMember(consultationId, currentUserId) == 0) {
            throw new BusinessException(403, "you are not consultation member");
        }
    }

    private String normalizeMessageType(String messageType, String fallback) {
        String val = trimToNull(messageType);
        if (val == null) {
            return fallback;
        }
        String upper = val.toUpperCase(Locale.ROOT);
        if (!SUPPORTED_MESSAGE_TYPES.contains(upper)) {
            throw new BusinessException(400, "unsupported messageType: " + messageType);
        }
        return upper;
    }

    private long[] normalizePair(Long userId, Long friendId) {
        long a = Math.min(userId, friendId);
        long b = Math.max(userId, friendId);
        return new long[]{a, b};
    }

    private String buildAttachmentObjectName(Long consultationId, String originalFilename) {
        String fileName = StringUtils.hasText(originalFilename) ? originalFilename : "attachment.bin";
        String safeName = fileName.replaceAll("[\\\\/\\s]+", "_");
        return "consultation/" + consultationId + "/" + System.currentTimeMillis() + "-" + safeName;
    }

    private String trimToNull(String value) {
        if (!StringUtils.hasText(value)) {
            return null;
        }
        return value.trim();
    }
}
