package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.dto.ConsultationCreateRequest;
import com.yunchuan.smartimage_backend.dto.ConsultationMessageSendRequest;
import com.yunchuan.smartimage_backend.security.SecurityUtil;
import com.yunchuan.smartimage_backend.service.SocialService;
import com.yunchuan.smartimage_backend.vo.ConsultationMemberVO;
import com.yunchuan.smartimage_backend.vo.ConsultationMessageVO;
import com.yunchuan.smartimage_backend.vo.ConsultationVO;
import com.yunchuan.smartimage_backend.vo.DoctorSimpleVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/patients/social")
public class SocialController {

    private final SocialService socialService;

    public SocialController(SocialService socialService) {
        this.socialService = socialService;
    }

    @GetMapping("/doctors")
    public ApiResponse<List<DoctorSimpleVO>> searchDoctors(@RequestParam(value = "keyword", required = false) String keyword,
                                                           HttpServletRequest request) {
        return ApiResponse.success(socialService.searchDoctors(SecurityUtil.currentUserId(request), keyword));
    }

    @GetMapping("/friends")
    public ApiResponse<List<DoctorSimpleVO>> listFriends(HttpServletRequest request) {
        return ApiResponse.success(socialService.listFriends(SecurityUtil.currentUserId(request)));
    }

    @PostMapping("/friends/{friendId}")
    public ApiResponse<Void> addFriend(@PathVariable("friendId") Long friendId,
                                       HttpServletRequest request) {
        socialService.addFriend(SecurityUtil.currentUserId(request), friendId);
        return ApiResponse.success(null);
    }

    @DeleteMapping("/friends/{friendId}")
    public ApiResponse<Void> removeFriend(@PathVariable("friendId") Long friendId,
                                          HttpServletRequest request) {
        socialService.removeFriend(SecurityUtil.currentUserId(request), friendId);
        return ApiResponse.success(null);
    }

    @GetMapping("/consultations")
    public ApiResponse<List<ConsultationVO>> listConsultations(HttpServletRequest request) {
        return ApiResponse.success(socialService.listConsultations(SecurityUtil.currentUserId(request)));
    }

    @PostMapping("/consultations")
    public ApiResponse<ConsultationVO> createConsultation(@Valid @RequestBody ConsultationCreateRequest requestBody,
                                                          HttpServletRequest request) {
        return ApiResponse.success(socialService.createConsultation(SecurityUtil.currentUserId(request), requestBody));
    }

    @GetMapping("/consultations/{consultationId}/members")
    public ApiResponse<List<ConsultationMemberVO>> listMembers(@PathVariable("consultationId") Long consultationId,
                                                               HttpServletRequest request) {
        return ApiResponse.success(socialService.listMembers(consultationId, SecurityUtil.currentUserId(request)));
    }

    @PostMapping("/consultations/{consultationId}/members/{doctorId}")
    public ApiResponse<Void> addMember(@PathVariable("consultationId") Long consultationId,
                                       @PathVariable("doctorId") Long doctorId,
                                       HttpServletRequest request) {
        socialService.addMember(consultationId, doctorId, SecurityUtil.currentUserId(request));
        return ApiResponse.success(null);
    }

    @DeleteMapping("/consultations/{consultationId}/members/{doctorId}")
    public ApiResponse<Void> removeMember(@PathVariable("consultationId") Long consultationId,
                                          @PathVariable("doctorId") Long doctorId,
                                          HttpServletRequest request) {
        socialService.removeMember(consultationId, doctorId, SecurityUtil.currentUserId(request));
        return ApiResponse.success(null);
    }

    @GetMapping("/consultations/{consultationId}/messages")
    public ApiResponse<List<ConsultationMessageVO>> listMessages(@PathVariable("consultationId") Long consultationId,
                                                                 @RequestParam(value = "beforeId", required = false) Long beforeId,
                                                                 @RequestParam(value = "limit", required = false) Integer limit,
                                                                 HttpServletRequest request) {
        return ApiResponse.success(socialService.listMessages(consultationId, SecurityUtil.currentUserId(request), beforeId, limit));
    }

    @PostMapping("/consultations/{consultationId}/messages")
    public ApiResponse<ConsultationMessageVO> sendMessage(@PathVariable("consultationId") Long consultationId,
                                                          @RequestBody ConsultationMessageSendRequest requestBody,
                                                          HttpServletRequest request) {
        return ApiResponse.success(socialService.sendMessage(consultationId, SecurityUtil.currentUserId(request), requestBody));
    }

    @PostMapping(value = "/consultations/{consultationId}/attachments", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<ConsultationMessageVO> uploadAttachment(@PathVariable("consultationId") Long consultationId,
                                                               @RequestParam("file") MultipartFile file,
                                                               @RequestParam(value = "messageType", required = false) String messageType,
                                                               HttpServletRequest request) {
        return ApiResponse.success(socialService.uploadAttachment(consultationId, SecurityUtil.currentUserId(request), file, messageType));
    }
}
