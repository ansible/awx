import { isAuthenticated } from './auth';

const invalidCookie = 'invalid';
const validLoggedOutCookie =
  'current_user=%7B%22id%22%3A1%2C%22type%22%3A%22user%22%2C%22url%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2F%22%2C%22related%22%3A%7B%22admin_of_organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fadmin_of_organizations%2F%22%2C%22authorized_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fauthorized_tokens%2F%22%2C%22roles%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Froles%2F%22%2C%22organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Forganizations%2F%22%2C%22access_list%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Faccess_list%2F%22%2C%22teams%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fteams%2F%22%2C%22tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Ftokens%2F%22%2C%22personal_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fpersonal_tokens%2F%22%2C%22credentials%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fcredentials%2F%22%2C%22activity_stream%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Factivity_stream%2F%22%2C%22projects%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fprojects%2F%22%7D%2C%22summary_fields%22%3A%7B%7D%2C%22created%22%3A%222018-10-19T16%3A30%3A59.141963Z%22%2C%22username%22%3A%22admin%22%2C%22first_name%22%3A%22%22%2C%22last_name%22%3A%22%22%2C%22email%22%3A%22%22%2C%22is_superuser%22%3Atrue%2C%22is_system_auditor%22%3Afalse%2C%22ldap_dn%22%3A%22%22%2C%22external_account%22%3Anull%2C%22auth%22%3A%5B%5D%7D; userLoggedIn=false; csrftoken=lhOHpLQUFHlIVqx8CCZmEpdEZAz79GIRBIT3asBzTbPE7HS7wizt7WBsgJClz8Ge';
const validLoggedInCookie =
  'current_user=%7B%22id%22%3A1%2C%22type%22%3A%22user%22%2C%22url%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2F%22%2C%22related%22%3A%7B%22admin_of_organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fadmin_of_organizations%2F%22%2C%22authorized_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fauthorized_tokens%2F%22%2C%22roles%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Froles%2F%22%2C%22organizations%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Forganizations%2F%22%2C%22access_list%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Faccess_list%2F%22%2C%22teams%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fteams%2F%22%2C%22tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Ftokens%2F%22%2C%22personal_tokens%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fpersonal_tokens%2F%22%2C%22credentials%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fcredentials%2F%22%2C%22activity_stream%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Factivity_stream%2F%22%2C%22projects%22%3A%22%2Fapi%2Fv2%2Fusers%2F1%2Fprojects%2F%22%7D%2C%22summary_fields%22%3A%7B%7D%2C%22created%22%3A%222018-10-19T16%3A30%3A59.141963Z%22%2C%22username%22%3A%22admin%22%2C%22first_name%22%3A%22%22%2C%22last_name%22%3A%22%22%2C%22email%22%3A%22%22%2C%22is_superuser%22%3Atrue%2C%22is_system_auditor%22%3Afalse%2C%22ldap_dn%22%3A%22%22%2C%22external_account%22%3Anull%2C%22auth%22%3A%5B%5D%7D; userLoggedIn=true; csrftoken=lhOHpLQUFHlIVqx8CCZmEpdEZAz79GIRBIT3asBzTbPE7HS7wizt7WBsgJClz8Ge';

describe('isAuthenticated', () => {
  test('returns false for invalid cookie', () => {
    expect(isAuthenticated(invalidCookie)).toEqual(false);
  });

  test('returns false for expired cookie', () => {
    expect(isAuthenticated(validLoggedOutCookie)).toEqual(false);
  });

  test('returns true for valid authenticated cookie', () => {
    expect(isAuthenticated(validLoggedInCookie)).toEqual(true);
  });
});
