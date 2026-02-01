package com.yunchuan.smartimage_backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

@Service
public class ModelSegmentService {

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public ModelSegmentService(@Value("${model-service.base-url:http://localhost:5001}") String baseUrl) {
        this.restTemplate = new RestTemplate();
        this.baseUrl = normalizeBaseUrl(baseUrl);
    }

    public byte[] segmentNrrd(byte[] payload, String filename) {
        if (payload == null || payload.length == 0) {
            throw new IllegalArgumentException("Empty NRRD payload");
        }
        String name = StringUtils.hasText(filename) ? filename : "input.nrrd";
        if (!name.toLowerCase().endsWith(".nrrd")) {
            name = name + ".nrrd";
        }
        final String finalName = name;

        ByteArrayResource resource = new ByteArrayResource(payload) {
            @Override
            public String getFilename() {
                return finalName;
            }
        };
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);
        ResponseEntity<byte[]> response = restTemplate.postForEntity(
                baseUrl + "/api/segment/nrrd",
                request,
                byte[].class
        );

        if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
            throw new RuntimeException("Model service failed with status: " + response.getStatusCode());
        }
        return response.getBody();
    }

    public byte[] segmentMultimodal(byte[] flair, String flairName,
                                    byte[] t1, String t1Name,
                                    byte[] t1c, String t1cName,
                                    byte[] t2, String t2Name) {
        if (flair == null || flair.length == 0 ||
                t1 == null || t1.length == 0 ||
                t1c == null || t1c.length == 0 ||
                t2 == null || t2.length == 0) {
            throw new IllegalArgumentException("Empty multimodal payload");
        }

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("flair", buildFileResource(flair, flairName, "flair.nrrd"));
        body.add("t1", buildFileResource(t1, t1Name, "t1.nrrd"));
        body.add("t1c", buildFileResource(t1c, t1cName, "t1c.nrrd"));
        body.add("t2", buildFileResource(t2, t2Name, "t2.nrrd"));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);
        ResponseEntity<byte[]> response = restTemplate.postForEntity(
                baseUrl + "/api/segment/multimodal",
                request,
                byte[].class
        );

        if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
            throw new RuntimeException("Model service failed with status: " + response.getStatusCode());
        }
        return response.getBody();
    }

    private ByteArrayResource buildFileResource(byte[] payload, String filename, String fallbackName) {
        String name = StringUtils.hasText(filename) ? filename : fallbackName;
        if (!name.toLowerCase().endsWith(".nrrd")) {
            name = name + ".nrrd";
        }
        final String finalName = name;
        return new ByteArrayResource(payload) {
            @Override
            public String getFilename() {
                return finalName;
            }
        };
    }

    private String normalizeBaseUrl(String value) {
        if (value == null || value.isBlank()) {
            return "http://localhost:5001";
        }
        return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
    }
}
