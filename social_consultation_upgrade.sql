-- 增量升级脚本：医生好友 + 联合会诊 + 聊天消息
USE `smart_image`;

CREATE TABLE IF NOT EXISTS `doctor_friend` (
  `id`          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  `doctor_id`   BIGINT UNSIGNED NOT NULL,
  `friend_id`   BIGINT UNSIGNED NOT NULL,
  `created_by`  BIGINT UNSIGNED NOT NULL,
  `created_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_friend_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user`(`id`),
  CONSTRAINT `fk_friend_friend` FOREIGN KEY (`friend_id`) REFERENCES `doctor_user`(`id`),
  CONSTRAINT `fk_friend_creator` FOREIGN KEY (`created_by`) REFERENCES `doctor_user`(`id`),
  UNIQUE KEY `uk_doctor_friend_pair` (`doctor_id`, `friend_id`),
  INDEX `idx_friend_doctor` (`doctor_id`),
  INDEX `idx_friend_friend` (`friend_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生好友关系';

CREATE TABLE IF NOT EXISTS `consultation_session` (
  `id`                 BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  `title`              VARCHAR(128) NOT NULL,
  `patient_id`         BIGINT UNSIGNED DEFAULT NULL,
  `creator_id`         BIGINT UNSIGNED NOT NULL,
  `status`             VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  `materials_oss_path` VARCHAR(255) DEFAULT NULL,
  `created_at`         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_consult_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient`(`id`),
  CONSTRAINT `fk_consult_creator` FOREIGN KEY (`creator_id`) REFERENCES `doctor_user`(`id`),
  INDEX `idx_consult_creator` (`creator_id`),
  INDEX `idx_consult_patient` (`patient_id`),
  INDEX `idx_consult_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='联合会诊会话';

CREATE TABLE IF NOT EXISTS `consultation_member` (
  `id`               BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  `consultation_id`  BIGINT UNSIGNED NOT NULL,
  `doctor_id`        BIGINT UNSIGNED NOT NULL,
  `role`             VARCHAR(32) NOT NULL DEFAULT 'MEMBER',
  `joined_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_consult_member_session` FOREIGN KEY (`consultation_id`) REFERENCES `consultation_session`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_consult_member_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user`(`id`),
  UNIQUE KEY `uk_consult_member` (`consultation_id`, `doctor_id`),
  INDEX `idx_consult_member_doctor` (`doctor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会诊成员';

CREATE TABLE IF NOT EXISTS `consultation_message` (
  `id`               BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  `consultation_id`  BIGINT UNSIGNED NOT NULL,
  `sender_id`        BIGINT UNSIGNED NOT NULL,
  `message_type`     VARCHAR(16) NOT NULL DEFAULT 'TEXT',
  `text_content`     TEXT DEFAULT NULL,
  `oss_path`         VARCHAR(255) DEFAULT NULL,
  `file_name`        VARCHAR(128) DEFAULT NULL,
  `file_size`        BIGINT DEFAULT NULL,
  `mime_type`        VARCHAR(128) DEFAULT NULL,
  `created_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_consult_message_session` FOREIGN KEY (`consultation_id`) REFERENCES `consultation_session`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_consult_message_sender` FOREIGN KEY (`sender_id`) REFERENCES `doctor_user`(`id`),
  INDEX `idx_consult_message_session` (`consultation_id`, `id`),
  INDEX `idx_consult_message_sender` (`sender_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会诊聊天消息';
