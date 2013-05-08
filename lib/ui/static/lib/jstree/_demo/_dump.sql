CREATE TABLE IF NOT EXISTS `tree` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `parent_id` bigint(20) unsigned NOT NULL,
  `position` bigint(20) unsigned NOT NULL,
  `left` bigint(20) unsigned NOT NULL,
  `right` bigint(20) unsigned NOT NULL,
  `level` bigint(20) unsigned NOT NULL,
  `title` text CHARACTER SET utf8 COLLATE utf8_unicode_ci,
  `type` varchar(255) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=13 ;

INSERT INTO `tree` (`id`, `parent_id`, `position`, `left`, `right`, `level`, `title`, `type`) VALUES
(1, 0, 2, 1, 14, 0, 'ROOT', ''),
(2, 1, 0, 2, 11, 1, 'C:', 'drive'),
(3, 2, 0, 3, 6, 2, '_demo', 'folder'),
(4, 3, 0, 4, 5, 3, 'index.html', 'default'),
(5, 2, 1, 7, 10, 2, '_docs', 'folder'),
(6, 1, 1, 12, 13, 1, 'D:', 'drive'),
(12, 5, 0, 8, 9, 3, 'zmei.html', 'default');
